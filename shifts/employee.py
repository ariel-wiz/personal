from __future__ import annotations

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DateRange:
    """Class to represent and handle date ranges with various utility methods"""
    date_start: str  # Format: dd/mm
    date_end: Optional[str] = None  # Format: dd/mm, if None, same as start

    def __post_init__(self):
        """Validate date format after initialization"""
        self._validate_date(self.date_start)
        self.date_end = self.date_end or self.date_start
        self._validate_date(self.date_end)

    @staticmethod
    def _validate_date(date_str: str):
        """Validate the date string format (dd/mm)"""
        try:
            day, month = map(int, date_str.split('/'))
            if not (1 <= day <= 31 and 1 <= month <= 12):
                raise ValueError
        except:
            raise ValueError(f"Invalid date format: {date_str}. Expected format: dd/mm")

    def get_full_dates(self) -> tuple[datetime.date, datetime.date]:
        """Convert dd/mm format to full dates using current/next year"""
        current_year = datetime.now().year
        start_day, start_month = map(int, self.date_start.split('/'))
        end_day, end_month = map(int, self.date_end.split('/'))

        # Adjust year if the date range crosses a year boundary
        start_year = current_year if start_month >= datetime.now().month else current_year + 1
        end_year = start_year if end_month >= start_month else start_year + 1

        return (
            datetime(start_year, start_month, start_day).date(),
            datetime(end_year, end_month, end_day).date()
        )

    def get_days_count(self) -> int:
        """Calculate the number of days in the range"""
        start_date, end_date = self.get_full_dates()
        return (end_date - start_date).days + 1

    def get_all_dates(self) -> List[datetime.date]:
        """Get all dates within the range"""
        start_date, end_date = self.get_full_dates()
        return [
            start_date + timedelta(days=x)
            for x in range((end_date - start_date).days + 1)
        ]

    def is_date_in_range(self, check_date: datetime.date) -> bool:
        """Check if a given date falls within this date range"""
        if isinstance(check_date, datetime):
            check_date = check_date.date()

        start_date, end_date = self.get_full_dates()
        return start_date <= check_date <= end_date

    def overlaps_with(self, other: 'DateRange') -> bool:
        """Check if this date range overlaps with another"""
        self_start, self_end = self.get_full_dates()
        other_start, other_end = other.get_full_dates()

        return (
                (self_start <= other_end and self_end >= other_start) or
                (other_start <= self_end and other_end >= self_start)
        )

    def merge_with(self, other: 'DateRange') -> Optional['DateRange']:
        """Merge with another date range if they overlap or are adjacent"""
        if not self.overlaps_with(other):
            return None

        self_start, self_end = self.get_full_dates()
        other_start, other_end = other.get_full_dates()

        new_start = min(self_start, other_start)
        new_end = max(self_end, other_end)

        return DateRange(
            new_start.strftime('%d/%m'),
            new_end.strftime('%d/%m')
        )

    def __str__(self) -> str:
        """Return string representation in format dd/mm-dd/mm (xd)"""
        if self.date_start == self.date_end:
            return f"{self.date_start} ({self.get_days_count()}d)"
        return f"{self.date_start}-{self.date_end} ({self.get_days_count()}d)"

    @staticmethod
    def get_consecutive_ranges(dates: List[datetime.date]) -> List['DateRange']:
        """Convert a list of dates into a list of consecutive date ranges"""
        if not dates:
            return []

        dates = sorted(dates)
        ranges = []
        range_start = range_end = dates[0]

        for i in range(1, len(dates)):
            if (dates[i] - range_end).days == 1:
                range_end = dates[i]
            else:
                # End current range
                ranges.append(DateRange(
                    range_start.strftime('%d/%m'),
                    range_end.strftime('%d/%m')
                ))
                range_start = range_end = dates[i]

        # Add final range
        ranges.append(DateRange(
            range_start.strftime('%d/%m'),
            range_end.strftime('%d/%m')
        ))

        return ranges


class Employee:
    def __init__(self,
                 name: str,
                 hebrew_names: str | List[str],
                 available_from: Optional[str] = None,
                 max_consecutive_home_days: int = 7,
                 min_consecutive_home_days: int = 5,
                 preferred_shift_partner: Optional[str] = None,
                 is_manager: bool = False,
                 is_shomer_shabat: bool = False,
                 must_day_at_home: Optional[List[DateRange]] = None,
                 wish_day_at_home: Optional[List[DateRange]] = None):
        """Initialize an Employee with their scheduling constraints and preferences."""
        self.name = name
        self.hebrew_names = [hebrew_names] if isinstance(hebrew_names, str) else hebrew_names
        self.available_from = (
            datetime.strptime(available_from, '%Y-%m-%d').date()
            if available_from else datetime.now().date()
        )
        self.max_consecutive_home_days = max_consecutive_home_days
        self.min_consecutive_home_days = min_consecutive_home_days
        self.preferred_shift_partner = preferred_shift_partner
        self.is_manager = is_manager
        self.is_shomer_shabat = is_shomer_shabat
        self.must_day_at_home = must_day_at_home or []
        self.wish_day_at_home = wish_day_at_home or []
        self._id = None

        # Initialize tracking attributes
        self.days_at_home: List[DateRange] = []
        self.days_at_shift: List[DateRange] = []
        self.total_home_days = 0
        self.total_shifts_days = 0

    def add_shift_day(self, date: datetime.date):
        """Add a day to shift schedule"""
        if isinstance(date, datetime):
            date = date.date()

        date_str = date.strftime('%d/%m')
        single_day_range = DateRange(date_str)

        # Update total count
        self.total_shifts_days += 1

        # Try to merge with existing ranges
        for i, existing_range in enumerate(self.days_at_shift):
            merged = existing_range.merge_with(single_day_range)
            if merged:
                self.days_at_shift[i] = merged
                return

        # If no merge possible, add as new range
        self.days_at_shift.append(single_day_range)
        self.days_at_shift.sort(key=lambda x: x.get_full_dates()[0])

    def add_home_day(self, date: datetime.date):
        """Add a day to home schedule"""
        if isinstance(date, datetime):
            date = date.date()

        date_str = date.strftime('%d/%m')
        single_day_range = DateRange(date_str)

        # Update total count
        self.total_home_days += 1

        # Try to merge with existing ranges
        for i, existing_range in enumerate(self.days_at_home):
            merged = existing_range.merge_with(single_day_range)
            if merged:
                self.days_at_home[i] = merged
                return

        # If no merge possible, add as new range
        self.days_at_home.append(single_day_range)
        self.days_at_home.sort(key=lambda x: x.get_full_dates()[0])

    @property
    def home_shift_ratio(self) -> int:
        """Calculate grade (0-100) representing the ratio between home and shift days"""
        total_days = self.total_home_days + self.total_shifts_days
        if total_days == 0:
            return 0
        return round((self.total_home_days / total_days) * 100)

    def get_total_days_since_available(self, current_date: datetime.date) -> int:
        """Calculate total days since employee became available"""
        if current_date < self.available_from:
            return 0
        return (current_date - self.available_from).days + 1

    def get_total_home_days_since_available(self, current_date: datetime.date) -> int:
        """Get total home days since employee became available"""
        if current_date < self.available_from:
            return 0

        total = 0
        for date_range in self.days_at_home:
            start_date, end_date = date_range.get_full_dates()
            # Adjust range to employee's availability
            start_date = max(start_date, self.available_from)
            end_date = min(end_date, current_date)
            if start_date <= end_date:
                total += (end_date - start_date).days + 1
        return total

    def get_total_shift_days_since_available(self, current_date: datetime.date) -> int:
        """Get total shift days since employee became available"""
        if current_date < self.available_from:
            return 0

        total = 0
        for date_range in self.days_at_shift:
            start_date, end_date = date_range.get_full_dates()
            # Adjust range to employee's availability
            start_date = max(start_date, self.available_from)
            end_date = min(end_date, current_date)
            if start_date <= end_date:
                total += (end_date - start_date).days + 1
        return total

    def get_home_shift_ratio(self, current_date: datetime.date) -> int:
        """Calculate grade (0-100) representing the ratio between home and shift days since available"""
        if current_date < self.available_from:
            return 0

        total_home = self.get_total_home_days_since_available(current_date)
        total_shift = self.get_total_shift_days_since_available(current_date)
        total_days = total_home + total_shift

        if total_days == 0:
            return 0
        return round((total_home / total_days) * 100)

    def get_days_difference_from_average(self, current_date: datetime.date, average_grade: float) -> float:
        """Calculate how many days difference from the average grade considering availability"""
        if current_date < self.available_from:
            return 0.0

        total_home = self.get_total_home_days_since_available(current_date)
        total_shift = self.get_total_shift_days_since_available(current_date)
        total_days = total_home + total_shift

        if total_days == 0:
            return 0.0

        expected_home_days = (average_grade / 100) * total_days
        return round(total_home - expected_home_days, 1)

    def is_available(self, date: datetime.date) -> bool:
        """Check if employee is available on a specific date"""
        if isinstance(date, datetime):
            date = date.date()

        # Check if date is before availability start
        if date < self.available_from:
            return False

        # Check if employee observes Shabbat and if the date is a Saturday
        if self.is_shomer_shabat and date.weekday() == 5:  # 5 represents Saturday
            return False

        # Check mandatory home days
        for date_range in self.must_day_at_home:
            if date_range.is_date_in_range(date):
                return False

        return True

    def prefers_home(self, date: datetime.date) -> bool:
        """Check if employee prefers to be at home on a specific date"""
        if isinstance(date, datetime):
            date = date.date()

        for date_range in self.wish_day_at_home:
            if date_range.is_date_in_range(date):
                return True

        return False

    def to_dict(self) -> dict:
        """Convert employee data to dictionary format"""
        return {
            'name': self.name,
            'hebrew_names': self.hebrew_names,
            'available_from': self.available_from.strftime('%Y-%m-%d'),
            'max_consecutive_home_days': self.max_consecutive_home_days,
            'min_consecutive_home_days': self.min_consecutive_home_days,
            'preferred_shift_partner': self.preferred_shift_partner,
            'is_manager': self.is_manager,
            'is_shomer_shabat': self.is_shomer_shabat,
            'must_day_at_home': [
                {'date_start': dr.date_start, 'date_end': dr.date_end}
                for dr in self.must_day_at_home
            ],
            'wish_day_at_home': [
                {'date_start': dr.date_start, 'date_end': dr.date_end}
                for dr in self.wish_day_at_home
            ],
            'num_days_at_home': self.num_days_at_home,
            'num_days_at_shift': self.num_days_at_shift,
            'days_at_home': [
                {'date_start': dr.date_start, 'date_end': dr.date_end}
                for dr in self.days_at_home
            ],
            'days_at_shift': [
                {'date_start': dr.date_start, 'date_end': dr.date_end}
                for dr in self.days_at_shift
            ]
        }