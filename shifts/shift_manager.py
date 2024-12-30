import sqlite3
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional
import random
import pandas as pd
from tabulate import tabulate

from shifts.employee import DateRange, Employee
from shifts.logger import ShiftLogger
from shifts.shift_data import EMPLOYEES


@dataclass
class EmployeeState:
    consecutive_home_days: int
    consecutive_shift_days: int
    total_shifts: int
    employee: object
    shift_history: List[datetime.date] = None

    def __post_init__(self):
        self.shift_history = []

    def add_shift(self, date: datetime.date):
        self.shift_history.append(date)
        self.shift_history.sort()

    def current_shift_streak(self) -> int:
        if not self.shift_history:
            return 0

        streak = 1
        for i in range(len(self.shift_history) - 1, 0, -1):
            if (self.shift_history[i] - self.shift_history[i - 1]).days == 1:
                streak += 1
            else:
                break
        return streak

@dataclass
class ScheduleResult:
    """Class to store schedule results with constraint information"""
    schedule: Dict[datetime.date, Set[str]]
    satisfied_constraints: Dict[datetime.date, List[str]]
    violated_constraints: Dict[datetime.date, List[str]]
    overall_score: float

    def __str__(self):
        return f"Schedule (score: {self.overall_score})"


class ScheduleConstraints:
    MIN_HOME_DAYS = 4  # Minimum consecutive days at home
    MAX_SHIFT_DAYS = 14  # Maximum consecutive days on shift
    REQUIRED_SHIFT_SIZE = 8  # Required number of employees per shift

    @staticmethod
    def check_mandatory_constraints(employee_state: EmployeeState, date: datetime.date) -> Tuple[bool, List[str], List[str]]:
        """Check if all mandatory constraints are satisfied for an employee on a given date"""
        satisfied = []
        violated = []

        # Check minimum consecutive home days
        if (employee_state.consecutive_home_days > 0 and
                employee_state.consecutive_home_days < ScheduleConstraints.MIN_HOME_DAYS):
            violated.append(f"Must complete minimum {ScheduleConstraints.MIN_HOME_DAYS} days at home")
        else:
            satisfied.append("Minimum home days met")

        # Check maximum consecutive shift days
        if employee_state.consecutive_shift_days >= ScheduleConstraints.MAX_SHIFT_DAYS - 1:
            violated.append(f"Max consecutive shift days ({ScheduleConstraints.MAX_SHIFT_DAYS})")
        else:
            satisfied.append("Within shift limits")

        # Check if employee has mandatory home days
        for date_range in employee_state.employee.must_day_at_home:
            if date_range.is_date_in_range(date):
                violated.append(f"Mandatory home day {date_range}")
                break

        # For Shabbat-observant employees, check transitions
        if employee_state.employee.is_shomer_shabat and date.weekday() == 5:
            # Get yesterday's status
            yesterday = date - timedelta(days=1)
            was_on_shift = any(shift_range.is_date_in_range(yesterday)
                             for shift_range in employee_state.employee.days_at_shift)
            will_be_on_shift = True  # Since we're checking for shift assignment

            if was_on_shift != will_be_on_shift:
                violated.append("Cannot travel on Shabbat")

        return len(violated) == 0, satisfied, violated


class WeightedConditions:
    """Class handling weighted optional conditions for schedule optimization"""

    def __init__(self, weights: Dict[str, int] = None):
        self.weights = weights or {
            'consecutive_shift': 7,      # Penalty for consecutive shift days
            'total_shifts': 8,           # Penalty for having more shifts than average
            'partner_preference': 6,     # Bonus for preferred partner pairs
            'home_days_balance': 5,      # Weight for maintaining fair home/shift balance
            'wish_day_at_home': 4,       # Bonus for respecting optional home day preferences
        }

    def calculate_score(self, employee_state: EmployeeState, date: datetime.date, avg_shifts: float) -> Tuple[float, List[str]]:
        """Calculate a weighted score for an employee based on various conditions"""
        score = 0
        satisfied_conditions = []

        # Penalize long consecutive shifts
        if employee_state.consecutive_shift_days > 5:
            score -= self.weights['consecutive_shift'] * employee_state.consecutive_shift_days
        else:
            satisfied_conditions.append("No long consecutive shifts")

        # Penalize having more shifts than average
        shift_diff = employee_state.total_shifts - avg_shifts
        if shift_diff > 0:
            score -= self.weights['total_shifts'] * shift_diff
        else:
            satisfied_conditions.append("Below average shifts")

        # Bonus for preferred partners
        if employee_state.employee.preferred_shift_partner:
            score += self.weights['partner_preference']
            satisfied_conditions.append("Preferred partner available")

        # Bonus for respecting wish_day_at_home
        if employee_state.employee.prefers_home(date):
            score += self.weights['wish_day_at_home']
            satisfied_conditions.append("Optional home day preference")

        return score, satisfied_conditions


class ShiftScheduler:
    def __init__(self, database_path='shift_schedule.db'):
        self.conn = sqlite3.connect(database_path)
        self.employees = {}
        self.logger = ShiftLogger()
        self.create_tables()
        self.logger.info("ShiftScheduler initialized")


    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            constraints_json TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule_history (
            id INTEGER PRIMARY KEY,
            employee_id INTEGER,
            period_start DATE,
            period_end DATE,
            days_on_shift INTEGER,
            days_at_home INTEGER,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS current_schedule (
            id INTEGER PRIMARY KEY,
            employee_id INTEGER,
            shift_date DATE,
            is_on_shift BOOLEAN,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
        ''')

        self.conn.commit()

    def add_employee(self, employee):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM employees WHERE name = ?', (employee.name,))
        existing = cursor.fetchone()

        if existing:
            employee._id = existing[0]
            self.employees[employee.name] = employee
            return existing[0]

        constraints_json = json.dumps(employee.to_dict())
        cursor.execute('''
        INSERT INTO employees (name, constraints_json) 
        VALUES (?, ?)
        ''', (employee.name, constraints_json))

        employee_id = cursor.lastrowid
        employee._id = employee_id
        self.employees[employee.name] = employee

        self.conn.commit()
        return employee_id

    def generate_fair_schedule(self, days: int, start_date: datetime.date = None, weights: Dict[str, int] = None,
                               num_schedules: int = 3) -> List[ScheduleResult]:
        """Generate multiple fair schedules for the specified number of days"""
        current_date = start_date or self._get_next_schedule_date()
        end_date = current_date + timedelta(days=days - 1)

        potential_schedules = []
        attempts = num_schedules * 3  # Try more times than needed to find best options

        for _ in range(attempts):
            try:
                result = self._generate_single_schedule(current_date, end_date, weights)
                potential_schedules.append(result)
            except RuntimeError as e:
                continue

        # Sort by overall score and return top schedules
        potential_schedules.sort(key=lambda x: x.overall_score, reverse=True)
        return potential_schedules[:num_schedules]

    def _generate_single_schedule(self, start_date: datetime.date, end_date: datetime.date,
                                  weights: Dict[str, int] = None) -> ScheduleResult:
        """Generate a single schedule with constraint tracking"""
        states = self._initialize_employee_states()
        weighted_conditions = WeightedConditions(weights)
        current_date = start_date

        schedule = {}
        satisfied_constraints = {}
        violated_constraints = {}
        overall_score = 0

        while current_date <= end_date:
            selected, daily_score, satisfied, violated = self._select_shift_employees_with_backtracking(
                current_date, states, weighted_conditions)

            if len(selected) != ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                raise RuntimeError(f"Failed to generate valid schedule for {current_date}")

            schedule[current_date] = selected
            satisfied_constraints[current_date] = satisfied
            violated_constraints[current_date] = violated
            overall_score += daily_score

            self._record_shift_assignments(current_date, selected, states)
            current_date += timedelta(days=1)

        self.conn.commit()
        return ScheduleResult(schedule, satisfied_constraints, violated_constraints, overall_score)

    def _select_shift_employees_with_backtracking(self, date: datetime.date,
                                                  states: Dict[str, EmployeeState],
                                                  weighted_conditions: WeightedConditions,
                                                  depth: int = 0) -> Tuple[Set[str], float, List[str], List[str]]:
        """Select shift employees with partner preferences and day request tracking"""
        if depth > 100:
            return set(), 0.0, [], ["Max recursion depth exceeded"]

        available_employees = []
        satisfied_constraints = []
        violated_constraints = []
        avg_shifts = sum(state.total_shifts for state in states.values()) / len(states)

        # Track day requests
        day_request_status = {}

        for name, state in states.items():
            emp = state.employee
            can_be_scheduled = True

            # Check mandatory home days
            for date_range in emp.must_day_at_home:
                if date_range.is_date_in_range(date):
                    violated_constraints.append(f"{name}: Must be home during {date_range}")
                    day_request_status[name] = "Mandatory home day respected"
                    can_be_scheduled = False
                    break

            if not can_be_scheduled:
                continue

            # Calculate consecutive days using the strict method
            consecutive_home_days = self._calculate_consecutive_days(name, date - timedelta(days=1), False)
            consecutive_shift_days = self._calculate_consecutive_days(name, date - timedelta(days=1), True)

            # Update state with accurate counts
            state.consecutive_home_days = consecutive_home_days
            state.consecutive_shift_days = consecutive_shift_days

            # Check minimum home days sequence
            if consecutive_home_days > 0 and consecutive_home_days < ScheduleConstraints.MIN_HOME_DAYS:
                violated_constraints.append(
                    f"{name}: Must complete minimum {ScheduleConstraints.MIN_HOME_DAYS} days at home "
                    f"(currently at {consecutive_home_days})"
                )
                can_be_scheduled = False

            # Check wish day at home
            for date_range in emp.wish_day_at_home:
                if date_range.is_date_in_range(date):
                    day_request_status[name] = "Optional home day request denied"
                    break

            if can_be_scheduled:
                # Add to available employees list
                score, _ = weighted_conditions.calculate_score(state, date, avg_shifts)
                is_manager = emp.is_manager
                available_employees.append((score, name, state, is_manager))

        # Sort by score and manager status
        available_employees.sort(key=lambda x: (-x[0], -x[3]))

        def try_complete_schedule(partial_schedule: Set[str],
                                  remaining_employees: List[tuple],
                                  current_score: float) -> Tuple[Set[str], float]:
            """Try to complete schedule while respecting partner preferences"""
            if len(partial_schedule) == ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                # Check manager presence
                has_manager = any(states[emp].employee.is_manager for emp in partial_schedule)
                if not has_manager:
                    violated_constraints.append("No manager assigned to shift")
                    return set(), 0.0

                # Check partner preferences
                for emp_name in partial_schedule:
                    if not self._check_partner_preference(emp_name, partial_schedule):
                        violated_constraints.append(f"{emp_name}: Preferred partner not in shift")
                        return set(), 0.0

                return partial_schedule, current_score

            if not remaining_employees:
                return set(), 0.0

            for i, (score, name, state, is_manager) in enumerate(remaining_employees):
                new_schedule = partial_schedule | {name}

                # Early check for partner preference
                if not self._check_partner_preference(name, new_schedule):
                    continue

                result_schedule, result_score = try_complete_schedule(
                    new_schedule,
                    remaining_employees[i + 1:],
                    current_score + score
                )
                if result_schedule:
                    return result_schedule, result_score

            return set(), 0.0

        final_schedule, final_score = try_complete_schedule(set(), available_employees, 0.0)

        # Add day request status to constraints
        for name, status in day_request_status.items():
            if "respected" in status.lower():
                satisfied_constraints.append(f"{name}: {status}")
            else:
                violated_constraints.append(f"{name}: {status}")

        if len(final_schedule) != ScheduleConstraints.REQUIRED_SHIFT_SIZE:
            final_schedule, final_score, relaxed_satisfied, relaxed_violated = (
                self._select_shift_employees_with_relaxed_constraints(
                    date, states, weighted_conditions
                )
            )
            violated_constraints.extend(relaxed_violated)

        return final_schedule, final_score, satisfied_constraints, violated_constraints

    def _select_shift_employees_with_relaxed_constraints(self, date: datetime.date,
                                                         states: Dict[str, EmployeeState],
                                                         weighted_conditions: WeightedConditions
                                                         ) -> Tuple[Set[str], float, List[str], List[str]]:
        """Fallback method with slightly relaxed constraints to ensure we get 8 employees."""
        available_employees = []
        selected = set()
        total_score = 0.0
        satisfied_constraints = ["Using relaxed constraints"]
        violated_constraints = ["Unable to meet all strict constraints"]

        # First pass: get all eligible employees including those close to limits
        avg_shifts = sum(state.total_shifts for state in states.values()) / len(states)

        for name, state in states.items():
            if state.employee.is_available(date):  # Only check basic availability
                score, conditions = weighted_conditions.calculate_score(state, date, avg_shifts)
                available_employees.append((score, name, state))
                satisfied_constraints.extend(conditions)

        available_employees.sort(key=lambda x: x[0], reverse=True)

        # Ensure manager presence
        manager_added = False
        for score, name, state in available_employees:
            if state.employee.is_manager and len(selected) < ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                selected.add(name)
                total_score += score
                manager_added = True
                break

        if not manager_added:
            violated_constraints.append("No manager available")

        # Add remaining employees
        for score, name, state in available_employees:
            if len(selected) >= ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                break
            if name not in selected:
                selected.add(name)
                total_score += score

        if len(selected) < ScheduleConstraints.REQUIRED_SHIFT_SIZE:
            violated_constraints.append(
                f"Only found {len(selected)} employees (needed {ScheduleConstraints.REQUIRED_SHIFT_SIZE})")

        return selected, total_score, satisfied_constraints, violated_constraints

    def _calculate_consecutive_days(self, emp_name: str, target_date: datetime.date, is_shift: bool) -> int:
        """Calculate consecutive days strictly by walking backwards from target date"""
        cursor = self.conn.cursor()
        current_date = target_date
        count = 0

        while True:
            cursor.execute('''
                SELECT is_on_shift 
                FROM current_schedule cs
                JOIN employees e ON cs.employee_id = e.id
                WHERE e.name = ? AND shift_date = ?
            ''', (emp_name, current_date.strftime('%Y-%m-%d')))

            result = cursor.fetchone()
            if not result:
                break

            if (is_shift and not result[0]) or (not is_shift and result[0]):
                break

            count += 1
            current_date -= timedelta(days=1)

        return count

    def _check_partner_preference(self, emp_name: str, current_schedule: Set[str]) -> bool:
        """Check if preferred partner condition is satisfied"""
        emp = self.employees[emp_name]
        if emp.preferred_shift_partner:
            return emp.preferred_shift_partner in current_schedule
        return True

    def _get_next_schedule_date(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT MAX(shift_date) FROM current_schedule')
        last_date = cursor.fetchone()[0]
        return (datetime.strptime(last_date, '%Y-%m-%d').date() + timedelta(days=1)
                if last_date else datetime.now().date() + timedelta(days=1))

    def _initialize_employee_states(self):
        summary = self.get_schedule_summary()
        return {
            name: EmployeeState(
                consecutive_home_days=0,
                consecutive_shift_days=0,
                total_shifts=summary.get(name, {}).get('shifts_until_last', 0),
                employee=emp
            ) for name, emp in self.employees.items()
        }

    def _select_shift_employees(self, date: datetime.date, states: Dict[str, EmployeeState],
                                weighted_conditions: WeightedConditions) -> Set[str]:
        available_employees = []
        avg_shifts = sum(state.total_shifts for state in states.values()) / len(states)

        for name, state in states.items():
            if (ScheduleConstraints.check_mandatory_constraints(state, date) and
                    not ScheduleConstraints.would_exceed_max_shifts(state)):
                score = weighted_conditions.calculate_score(state, avg_shifts)
                available_employees.append((score, name, state))

        available_employees.sort(reverse=True)
        selected = set()

        # Ensure manager presence
        for score, name, state in available_employees:
            if state.employee.is_manager and len(selected) < ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                selected.add(name)
                break

        # Add partner pairs
        for score, name, state in available_employees:
            if len(selected) >= ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                break
            if name not in selected and state.employee.preferred_shift_partner:
                partner = next(
                    (entry for entry in available_employees if entry[1] == state.employee.preferred_shift_partner),
                    None
                )
                if partner and len(selected) <= ScheduleConstraints.REQUIRED_SHIFT_SIZE - 2:
                    selected.update([name, partner[1]])

        # Fill remaining slots while ensuring we don't create future violations
        for score, name, state in available_employees:
            if len(selected) >= ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                break
            if name not in selected:
                selected.add(name)

        return selected

    def _record_shift_assignments(self, date: datetime.date, selected: Set[str], states: Dict[str, EmployeeState]):
        for name, state in states.items():
            is_selected = name in selected
            self._record_schedule_entry(state.employee._id, date, is_selected)

            if is_selected:
                state.consecutive_home_days = 0
                state.consecutive_shift_days += 1
                state.total_shifts += 1
                state.add_shift(date)
            else:
                state.consecutive_home_days += 1
                state.consecutive_shift_days = 0

    def _shift_exists(self, employee_id, date):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM current_schedule 
            WHERE employee_id = ? AND shift_date = ?
        ''', (employee_id, date.strftime('%Y-%m-%d')))
        return cursor.fetchone()[0] > 0

    # Update the _record_schedule_entry method in ShiftScheduler
    def _record_schedule_entry(self, employee_id, date, is_on_shift):
        if not self._shift_exists(employee_id, date):
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO current_schedule 
                (employee_id, shift_date, is_on_shift) 
                VALUES (?, ?, ?)
            ''', (employee_id, date.strftime('%Y-%m-%d'), is_on_shift))

            employee = next(emp for emp in self.employees.values() if emp._id == employee_id)
            if is_on_shift:
                employee.add_shift_day(date)
            else:
                employee.add_home_day(date)

    def _get_schedule_range(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT MIN(shift_date), MAX(shift_date) FROM current_schedule')
        start_date_str, end_date_str = cursor.fetchone()
        return (
            datetime.strptime(start_date_str, '%Y-%m-%d').date(),
            datetime.strptime(end_date_str, '%Y-%m-%d').date()
        )

    def _calculate_streak(self, employee_name: str, current_date: datetime.date, is_on_shift: bool) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT shift_date, is_on_shift
            FROM current_schedule cs
            JOIN employees e ON cs.employee_id = e.id
            WHERE e.name = ? AND shift_date <= ?
            ORDER BY shift_date DESC
        ''', (employee_name, current_date.strftime('%Y-%m-%d')))

        streak = 1
        previous_records = cursor.fetchall()

        for i in range(1, len(previous_records)):
            if (previous_records[i][1] == is_on_shift and
                    datetime.strptime(previous_records[i - 1][0], '%Y-%m-%d').date() -
                    datetime.strptime(previous_records[i][0], '%Y-%m-%d').date() == timedelta(days=1)):
                streak += 1
            else:
                break

        return streak

    def verify_schedule_constraints(self, period_start, period_end):
        cursor = self.conn.cursor()
        violations = []

        current_date = period_start
        while current_date <= period_end:
            date_str = current_date.strftime('%Y-%m-%d')

            cursor.execute('''
                SELECT COUNT(*) 
                FROM current_schedule 
                WHERE shift_date = ? AND is_on_shift = 1
            ''', (date_str,))

            shift_count = cursor.fetchone()[0]

            if shift_count < 2:
                violations.append(f"Less than 2 employees on shift on {date_str}")
            if shift_count != ScheduleConstraints.REQUIRED_SHIFT_SIZE:
                violations.append(
                    f"Expected {ScheduleConstraints.REQUIRED_SHIFT_SIZE} employees on shift, got {shift_count} on {date_str}")

            current_date += timedelta(days=1)

        return len(violations) == 0, violations

    def _get_consecutive_days(self, emp_name: str, date: datetime.date, is_shift: bool) -> int:
        """Get consecutive days (shift or home) up to and including given date"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT shift_date, is_on_shift
            FROM current_schedule cs
            JOIN employees e ON cs.employee_id = e.id
            WHERE e.name = ? AND shift_date <= ?
            ORDER BY shift_date DESC
        ''', (emp_name, date.strftime('%Y-%m-%d')))

        records = cursor.fetchall()
        if not records:
            return 0

        consecutive_days = 0
        target_state = 1 if is_shift else 0

        # Process records day by day
        current_date = date
        for record in records:
            record_date = datetime.strptime(record[0], '%Y-%m-%d').date()
            record_state = record[1]

            # If there's a gap in dates or wrong state, break
            if record_date != current_date or record_state != target_state:
                break

            consecutive_days += 1
            current_date -= timedelta(days=1)

        return consecutive_days

    def _check_home_sequence(self, emp_name: str, date: datetime.date) -> int:
        """Get the current consecutive home days sequence, including planned days"""
        consecutive_days = self._get_consecutive_days(emp_name, date, False)
        return consecutive_days

    def _update_employee_states(self, states: Dict[str, EmployeeState], date: datetime.date):
        """Update employee states with accurate consecutive day counts"""
        for name, state in states.items():
            # Update consecutive days based on database records
            state.consecutive_home_days = self._get_consecutive_days(name, date - timedelta(days=1), False)
            state.consecutive_shift_days = self._get_consecutive_days(name, date - timedelta(days=1), True)

    def _get_current_schedule_range(self) -> Tuple[datetime.date, datetime.date]:
        """Get the date range of the currently loaded schedule"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT MIN(shift_date), MAX(shift_date) FROM current_schedule')
        min_date, max_date = cursor.fetchone()

        if not min_date or not max_date:
            return None, None

        return (
            datetime.strptime(min_date, '%Y-%m-%d').date(),
            datetime.strptime(max_date, '%Y-%m-%d').date()
        )

    def _get_schedule_for_date(self, date: datetime.date) -> Set[str]:
        """Get the set of employees on shift for a given date"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT e.name
            FROM current_schedule cs
            JOIN employees e ON cs.employee_id = e.id
            WHERE cs.shift_date = ? AND cs.is_on_shift = 1
        ''', (date.strftime('%Y-%m-%d'),))

        return set(row[0] for row in cursor.fetchall())

    def _get_constraints_for_date(self, date: datetime.date) -> Tuple[List[str], List[str]]:
        """Get satisfied and violated constraints for a date with improved accuracy"""
        satisfied = []
        violated = []

        # Get employees on shift for this date and previous date
        on_shift_today = self._get_schedule_for_date(date)
        on_shift_yesterday = self._get_schedule_for_date(date - timedelta(days=1))

        # Check each employee's constraints
        for name, emp in self.employees.items():
            # Skip if employee is not yet available
            if date < emp.available_from:
                continue

            is_on_shift_today = name in on_shift_today
            was_on_shift_yesterday = name in on_shift_yesterday

            # Check Shabbat constraints - only if there's a transition on Shabbat
            if emp.is_shomer_shabat and date.weekday() == 5:  # Saturday
                if is_on_shift_today != was_on_shift_yesterday:
                    violated.append(f"{name}: Cannot travel on Shabbat")
                else:
                    satisfied.append(f"{name}: Shabbat observance respected")

            # Check mandatory home days
            for date_range in emp.must_day_at_home:
                if date_range.is_date_in_range(date):
                    if not is_on_shift_today:
                        satisfied.append(f"{name}: Mandatory home day respected ({date_range})")
                    else:
                        violated.append(f"{name}: Must be home during {date_range}")

            # Check wish days
            for date_range in emp.wish_day_at_home:
                if date_range.is_date_in_range(date):
                    if not is_on_shift_today:
                        satisfied.append(f"{name}: Optional home day respected ({date_range})")
                    else:
                        violated.append(f"{name}: Optional home day request denied ({date_range})")

            # Check minimum consecutive home days - only report when sequence is broken
            if was_on_shift_yesterday and not is_on_shift_today:  # Starting home sequence
                continue  # Don't report yet, sequence just started
            elif not was_on_shift_yesterday and is_on_shift_today:  # Ending home sequence
                consecutive_home = self._get_consecutive_days(name, date - timedelta(days=1), False)
                min_days = emp.min_consecutive_home_days
                if consecutive_home < min_days:
                    violated.append(
                        f"{name}: Home sequence ended after {consecutive_home} days (minimum {min_days} required)")

            # Check partner preferences during transitions
            if emp.preferred_shift_partner and is_on_shift_today != was_on_shift_yesterday:
                partner_name = emp.preferred_shift_partner
                partner_on_shift_today = partner_name in on_shift_today
                partner_on_shift_yesterday = partner_name in on_shift_yesterday

                # Check if both employees are transitioning together
                if partner_on_shift_today != partner_on_shift_yesterday:
                    satisfied.append(f"{name}: Traveling with preferred partner {partner_name}")
                else:
                    violated.append(f"{name}: Traveling without preferred partner {partner_name}")

        return satisfied, violated

    def print_daily_schedule(self, start_date: datetime.date = None, end_date: datetime.date = None):
        """Print the current schedule from the database

        Args:
            start_date: Optional start date. If None, uses first date in schedule
            end_date: Optional end date. If None, uses last date in schedule
        """
        if start_date is None or end_date is None:
            db_start, db_end = self._get_current_schedule_range()
            start_date = start_date or db_start
            end_date = end_date or db_end

        if not start_date or not end_date:
            print("No schedule found in database")
            return

        # Create a ScheduleResult object from the current schedule
        schedule = {}
        satisfied_constraints = {}
        violated_constraints = {}

        current_date = start_date
        while current_date <= end_date:
            schedule[current_date] = self._get_schedule_for_date(current_date)
            satisfied, violated = self._get_constraints_for_date(current_date)
            satisfied_constraints[current_date] = satisfied
            violated_constraints[current_date] = violated
            current_date += timedelta(days=1)

        schedule_result = ScheduleResult(
            schedule=schedule,
            satisfied_constraints=satisfied_constraints,
            violated_constraints=violated_constraints,
            overall_score=0.0  # We don't recalculate score for existing schedule
        )

        # Use the existing print function
        self.print_daily_schedule_result(schedule_result, start_date, end_date)

    def print_daily_schedule_result(self, schedule_result: ScheduleResult, start_date: datetime.date,
                                    end_date: datetime.date):
        """Print function with improved constraint reporting"""
        WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        table_data = []
        current_date = start_date

        while current_date <= end_date:
            weekday = WEEKDAYS[current_date.weekday()]
            shift_emps = []
            home_emps = []

            # Process employees on shift
            for name in sorted(schedule_result.schedule.get(current_date, set())):
                emp = self.employees[name]
                if current_date < emp.available_from:
                    continue
                prefix = '*' if emp.is_manager else ''
                consecutive_days = self._calculate_consecutive_days(name, current_date, True)
                shift_emps.append(f"{prefix}{name} ({consecutive_days}d)")

            # Get employees at home
            all_emps = set(self.employees.keys())
            home_names = sorted(all_emps - set(schedule_result.schedule.get(current_date, set())))
            for name in home_names:
                emp = self.employees[name]
                if current_date < emp.available_from:
                    home_emps.append(f"{name} (N/A)")
                else:
                    consecutive_days = self._calculate_consecutive_days(name, current_date, False)
                    home_emps.append(f"{name} ({consecutive_days}d)")

            # Format constraints
            constraints_text = []
            if current_date in schedule_result.violated_constraints:
                violations = schedule_result.violated_constraints[current_date]
                if violations:
                    constraints_text.extend(f"✗ {v}" for v in violations)

            if current_date in schedule_result.satisfied_constraints:
                satisfied = schedule_result.satisfied_constraints[current_date]
                if satisfied:
                    if constraints_text:
                        constraints_text.append("")
                    constraints_text.extend(f"✓ {s}" for s in satisfied)

            table_data.append([
                f"{current_date.strftime('%d/%m/%Y')} ({weekday})",
                '\n'.join(shift_emps) if shift_emps else "-",
                '\n'.join(home_emps) if home_emps else "-",
                '\n'.join(constraints_text) if constraints_text else "No special constraints"
            ])

            current_date += timedelta(days=1)

        headers = ['Date', 'On Shift', 'At Home', 'Constraints']
        print(f"\nDaily Schedule (Score: {schedule_result.overall_score})")
        print(tabulate(table_data, headers=headers, tablefmt='grid'))

    def _calculate_total_days_up_to(self, employee_name: str, current_date: datetime.date, is_on_shift: bool) -> int:
        """Calculate total days either on shift or at home up to the given date"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COUNT(*)
            FROM current_schedule cs
            JOIN employees e ON cs.employee_id = e.id
            WHERE e.name = ? 
            AND cs.is_on_shift = ?
            AND cs.shift_date <= ?
        ''', (employee_name, is_on_shift, current_date.strftime('%Y-%m-%d')))

        return cursor.fetchone()[0]

    def get_schedule_summary(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, constraints_json FROM employees')
        employees = cursor.fetchall()
        summary = {}

        for emp_id, name, _ in employees:
            cursor.execute('''
                SELECT shift_date, is_on_shift
                FROM current_schedule
                WHERE employee_id = ?
                ORDER BY shift_date
            ''', (emp_id,))
            schedule = cursor.fetchall()

            shift_dates = [date for date, is_shift in schedule if is_shift]
            home_dates = [date for date, is_shift in schedule if not is_shift]

            cursor.execute('SELECT MAX(shift_date) FROM current_schedule')
            last_date = cursor.fetchone()[0]

            cursor.execute('''
                SELECT COUNT(*)
                FROM current_schedule
                WHERE employee_id = ? 
                AND is_on_shift = 1
                AND shift_date <= ?
            ''', (emp_id, last_date))
            shifts_until_last = cursor.fetchone()[0]

            summary[name] = {
                'shift_dates': shift_dates,
                'home_dates': home_dates,
                'total_shifts': len(shift_dates),
                'total_home_days': len(home_dates),
                'shifts_until_last': shifts_until_last
            }

        return summary

    def print_employee_summary(self):
        """Print summary of employee schedules with home/shift grade and days difference"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT MAX(shift_date) FROM current_schedule')
        current_date = datetime.strptime(cursor.fetchone()[0], '%Y-%m-%d').date()

        # Get active employees and calculate average grade
        active_employees = [
            emp for emp in self.employees.values()
            if emp.available_from <= current_date
        ]

        # Calculate weighted average grade based on available days
        total_weighted_grade = 0
        total_days = 0
        for emp in active_employees:
            emp_days = emp.get_total_days_since_available(current_date)
            if emp_days > 0:
                grade = emp.get_home_shift_ratio(current_date)
                total_weighted_grade += grade * emp_days
                total_days += emp_days

        average_grade = total_weighted_grade / total_days if total_days > 0 else 0

        table_data = []
        # Sort by home/shift ratio
        sorted_employees = sorted(active_employees,
                                  key=lambda emp: emp.get_home_shift_ratio(current_date))

        for emp in sorted_employees:
            total_home = emp.get_total_home_days_since_available(current_date)
            total_shift = emp.get_total_shift_days_since_available(current_date)

            current_streak = ""
            if emp.days_at_shift or emp.days_at_home:
                if emp.days_at_shift and (not emp.days_at_home or
                                          emp.days_at_shift[-1].get_full_dates()[1] >
                                          emp.days_at_home[-1].get_full_dates()[1]):
                    streak_days = self._calculate_streak(emp.name, current_date, True)
                    current_streak = f"({streak_days}d at shift)"
                else:
                    streak_days = self._calculate_streak(emp.name, current_date, False)
                    current_streak = f"({streak_days}d at home)"

            days_diff = emp.get_days_difference_from_average(current_date, average_grade)
            days_diff_str = f" ({days_diff:+.1f}d)" if days_diff != 0 else ""

            grade = emp.get_home_shift_ratio(current_date)

            row = [
                emp.name,
                total_shift,
                total_home,
                f"{grade}/{round(average_grade)}{days_diff_str}",
                current_streak,
                emp.available_from.strftime('%d/%m/%Y')
            ]
            table_data.append(row)

        headers = [
            'Employee',
            'Days at Shift',
            'Days at Home',
            'Grade/Avg (Diff)',
            'Current Streak',
            'Available From'
        ]
        print("\nEmployee Schedule Summary:")
        print(tabulate(table_data, headers=headers, tablefmt='grid', numalign='right'))
        print("\n* Grade: 100 = all days at home, 0 = all days at shift")
        print("* Diff: positive means more days at home than average, negative means more days at shift")

    def parse_hebrew_schedule(self, file_path):
        df = pd.read_excel(file_path)
        date_columns = df.columns[2:]
        home_row = df[df.iloc[:, 1] == "בית"].columns[0]

        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM current_schedule')

        # Reset all employee counters
        for emp in self.employees.values():
            emp.days_at_shift = []
            emp.days_at_home = []
            emp.total_shifts_days = 0
            emp.total_home_days = 0

        hebrew_to_employee = {}
        for emp in self.employees.values():
            for hebrew_name in emp.hebrew_names:
                hebrew_to_employee[hebrew_name] = emp

        for col in date_columns:
            date_str = str(col).strip()
            if '.' in date_str:
                day, month = map(int, date_str.split('.'))
                year = datetime.now().year
                if month < datetime.now().month:
                    year += 1
                current_date = datetime(year, month, day).date()

                shift_employees = df.iloc[:home_row - 3, df.columns.get_loc(col)]
                shift_employees = shift_employees.dropna().tolist()

                home_employees = df.iloc[home_row - 1:30, df.columns.get_loc(col)]
                home_employees = home_employees.dropna().tolist()

                processed_employees = set()

                for hebrew_name in shift_employees:
                    if hebrew_name in hebrew_to_employee:
                        employee = hebrew_to_employee[hebrew_name]
                        if employee.name not in processed_employees:
                            self._record_schedule_entry(employee._id, current_date, True)
                            processed_employees.add(employee.name)

                for hebrew_name in home_employees:
                    if hebrew_name in hebrew_to_employee:
                        employee = hebrew_to_employee[hebrew_name]
                        if employee.name not in processed_employees:
                            self._record_schedule_entry(employee._id, current_date, False)
                            processed_employees.add(employee.name)

        self.conn.commit()

    def close(self):
        self.conn.close()


def main():
    # Initialize scheduler
    scheduler = setup_scheduler()

    # Example usage:
    # 1. Print current status
    print_current_status(scheduler)

    # 2. Generate new schedules with custom parameters
    custom_weights = {
        'consecutive_shift': 8,  # Increased weight for consecutive shifts
        'total_shifts': 7,
        'partner_preference': 6,
        'home_days_balance': 6,  # Increased weight for balance
        'wish_day_at_home': 4,
    }

    start_date = datetime.now().date() + timedelta(days=1)
    schedules = generate_new_schedule(
        scheduler,
        start_date=start_date,
        weights=custom_weights,
        days=21,
        num_schedules=3
    )

    # Print final summary
    print("\nFinal Employee Summary:")
    print("----------------------")
    scheduler.print_employee_summary()

    # Close the database connection
    scheduler.close()


def setup_scheduler() -> ShiftScheduler:
    """Initialize the scheduler and add employees."""
    scheduler = ShiftScheduler()

    # Add all employees from the data file
    for employee in EMPLOYEES:
        scheduler.add_employee(employee)

    return scheduler


def print_current_status(scheduler: ShiftScheduler):
    """Print the current schedule status and employee summary."""
    # First, parse the existing Excel schedule if it exists
    try:
        print("\nParsing existing schedule...")
        scheduler.parse_hebrew_schedule("Syria 25 Team Maslow.xlsx")
    except Exception as e:
        print(f"Warning: Could not parse existing schedule: {e}")

    print("\nCurrent Schedule Status:")
    print("------------------------")
    scheduler.print_daily_schedule()

    print("\nEmployee Summary:")
    print("----------------")
    scheduler.print_employee_summary()


def generate_new_schedule(
        scheduler: ShiftScheduler,
        start_date: Optional[datetime.date] = None,
        weights: Optional[Dict[str, int]] = None,
        days: int = 21,
        num_schedules: int = 3
) -> List[Dict]:
    """
    Generate new schedules starting from a specific date with optional weights.

    Args:
        scheduler: Initialized ShiftScheduler instance
        start_date: Start date for the new schedule. If None, uses next available date
        weights: Optional dictionary of weights for different constraints
        days: Number of days to schedule (default 21)
        num_schedules: Number of schedule options to generate (default 3)

    Returns:
        List of generated schedules with their scores
    """
    # Use default weights if none provided
    if weights is None:
        weights = {
            'consecutive_shift': 7,
            'total_shifts': 8,
            'partner_preference': 6,
            'home_days_balance': 5,
            'wish_day_at_home': 4,
        }

    print(f"\nGenerating {num_schedules} schedule options for {days} days...")
    print("---------------------------------------------")

    # Generate schedules
    schedules = scheduler.generate_fair_schedule(
        days=days,
        start_date=start_date,
        weights=weights,
        num_schedules=num_schedules
    )

    # Print each schedule option
    results = []
    for i, schedule in enumerate(schedules, 1):
        print(f"\nSchedule Option {i}")
        print(f"Score: {schedule.overall_score:.2f}")
        print("=" * 50)

        start = min(schedule.schedule.keys())
        end = max(schedule.schedule.keys())
        scheduler.print_daily_schedule_result(schedule, start, end)

        results.append({
            'schedule': schedule,
            'score': schedule.overall_score,
            'start_date': start,
            'end_date': end
        })

    return results


if __name__ == "__main__":
    main()