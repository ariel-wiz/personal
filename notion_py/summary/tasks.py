from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional


from common import seconds_to_hours_minutes, parse_duration_to_seconds
from notion_py.helpers.notion_children_blocks import create_column_block, create_metrics_single_paragraph, \
    create_toggle_stats_block, create_two_column_section, create_section_text_with_bullet
from notion_py.helpers.notion_common import get_db_pages
from notion_py.summary.base_component import BaseComponent


class TasksComponent(BaseComponent):
    def __init__(self, daily_tasks_db_id: str, tasks_db_id: str, target_date: Optional[date] = None):
        super().__init__(target_date)
        self.daily_tasks_db_id = daily_tasks_db_id
        self.tasks_db_id = tasks_db_id

    def _initialize_metrics(self):
        """Initializes task metrics for the target date"""
        current_month_tasks = self._get_pages_for_month(self.tasks_db_id, self.target_date, date_property="Due")
        current_month_daily = self._get_pages_for_month(self.daily_tasks_db_id, self.target_date, date_property="Due")

        # Get previous month data
        previous_month = self.target_date.replace(day=1) - timedelta(days=1)
        previous_month_tasks = self._get_pages_for_month(self.tasks_db_id, previous_month, date_property="Due")
        previous_month_daily = self._get_pages_for_month(self.daily_tasks_db_id, previous_month, date_property="Due")

        # Calculate metrics for current month
        self._current_metrics = {
            **self._calculate_task_metrics(current_month_tasks, current_month_daily),
            'projects': self._get_project_breakdown(current_month_tasks)
        }

        # Calculate metrics for previous month
        self._previous_metrics = {
            **self._calculate_task_metrics(previous_month_tasks, previous_month_daily),
            'projects': self._get_project_breakdown(previous_month_tasks)
        }

    def _calculate_task_metrics(self, regular_tasks: List[Dict], daily_tasks: List[Dict]) -> Dict:
        """Calculates combined task metrics"""
        daily_stats = self._calculate_task_completion(daily_tasks)
        regular_stats = self._calculate_task_completion(regular_tasks)
        daily_creation_stats = self._get_daily_task_creation_stats(daily_tasks)

        return {
            'daily_completed': daily_stats['completed'],
            'daily_total': daily_stats['total'],
            'daily_completion_rate': daily_stats['completion_rate'],
            'daily_created': daily_creation_stats['total_created'],
            'regular_completed': regular_stats['completed'],
            'regular_total': regular_stats['total'],
            'regular_completion_rate': regular_stats['completion_rate'],
            'avg_completion_time': regular_stats['avg_completion_time'],
            'new_tasks': len(self._get_new_tasks_in_period(self.tasks_db_id, self.target_date)),
            'overdue_tasks': len(self._get_overdue_tasks(self.tasks_db_id))
        }

    def get_metrics(self) -> Dict:
        """Returns task metrics with comparisons"""
        return {
            'daily_completed': {
                'current': self.current_metrics['daily_completed'],
                'total': self.current_metrics['daily_total'],
                'rate': self.current_metrics['daily_completion_rate'],
                'comparison': self._format_comparison(
                    self.current_metrics['daily_completion_rate'],
                    self.previous_metrics['daily_completion_rate'],
                    'completion rate'
                )
            },
            'non_calendar_tasks': {
                'current': self.current_metrics['daily_created'],
                'comparison': self._format_comparison(
                    self.current_metrics['daily_created'],
                    self.previous_metrics['daily_created'],
                    'tasks created'
                )
            },
            'regular_tasks': {
                'completed': self.current_metrics['regular_completed'],
                'total': self.current_metrics['regular_total'],
                'rate': self.current_metrics['regular_completion_rate'],
                'avg_completion_time': self.current_metrics['avg_completion_time'],
                'completion_time_comparison': self._format_comparison(
                    parse_duration_to_seconds(self.current_metrics['avg_completion_time']),
                    parse_duration_to_seconds(self.previous_metrics['avg_completion_time']),
                    'completion time',
                    reverse_comparison=True
                )
            },
            'projects': self.current_metrics['projects']
        }

    def create_notion_section(self) -> dict:
        metrics = self.get_metrics()

        daily_section_bullets = [
            f"Completed: {metrics['daily_completed']['current']}/{metrics['daily_completed']['total']} "
            f"({metrics['daily_completed']['rate']}% {metrics['daily_completed']['comparison']})",
            f"Non-Calendar Tasks Created: {metrics['non_calendar_tasks']['current']} "
            f"({metrics['non_calendar_tasks']['comparison']})"
        ]

        regular_section_bullets = [
            f"Completed: {metrics['regular_tasks']['completed']}/{metrics['regular_tasks']['total']} "
            f"({metrics['regular_tasks']['rate']}%)",
            f"Average Completion Time: {metrics['regular_tasks']['avg_completion_time']} "
            f"({metrics['regular_tasks']['completion_time_comparison']})"
        ]

        daily_blocks = create_section_text_with_bullet("Daily Tasks:", daily_section_bullets)
        regular_blocks = create_section_text_with_bullet("Regular Tasks:", regular_section_bullets)

        project_stats = [
            f"{project['name']}: {project['completed']}/{project['total']} completed "
            f"({round((project['completed'] / project['total']) * 100 if project['total'] > 0 else 0, 1)}%)"
            for project in metrics['projects']
        ]

        left_column = create_column_block(
            "✅ Task Completion",
            [*daily_blocks, *regular_blocks]  # Unpack both sections' blocks
        )

        right_column = create_column_block(
            "Projects",
            [create_toggle_stats_block("Project Breakdown", project_stats)]
        )

        return create_two_column_section(left_column, right_column)
    def _create_project_breakdown_block(self, projects: List[Dict]) -> dict:
        """Creates a project breakdown toggle block for Notion

        Args:
            projects: List of project dictionaries with name, completed, and total stats
        """
        return {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Project Breakdown"}
                    }
                ],
                "children": [
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"{project['name']}: {project['completed']}/{project['total']} completed ({round((project['completed'] / project['total']) * 100 if project['total'] > 0 else 0, 1)}%)"
                                    }
                                }
                            ]
                        }
                    }
                    for project in projects
                ]
            }
        }
    def _calculate_task_completion(self, tasks: List[Dict]) -> Dict:
        """Calculates task completion statistics with completion time"""
        total = len(tasks)
        completed_tasks = []
        completion_times = []

        for task in tasks:
            if task['properties'].get('Done', {}).get('checkbox', False):
                completed_tasks.append(task)

                # Calculate completion time
                created_time = datetime.fromisoformat(task['created_time'].replace('Z', '+00:00'))
                last_edited = datetime.fromisoformat(task['last_edited_time'].replace('Z', '+00:00'))
                completion_time = last_edited - created_time
                completion_times.append(completion_time.total_seconds())

        avg_completion_time = (
            seconds_to_hours_minutes(sum(completion_times) / len(completion_times))
            if completion_times else "N/A"
        )

        return {
            'completed': len(completed_tasks),
            'total': total,
            'completion_rate': round((len(completed_tasks) / total * 100) if total > 0 else 0, 1),
            'avg_completion_time': avg_completion_time
        }

    def _get_project_breakdown(self, tasks: List[Dict]) -> List[Dict]:
        """Gets task completion breakdown by project"""
        projects = defaultdict(lambda: {'completed': 0, 'total': 0})

        for task in tasks:
            project = task['properties'].get('Project', {}).get('select', {}).get('name', 'Unassigned')
            projects[project]['total'] += 1
            if task['properties'].get('Done', {}).get('checkbox', False):
                projects[project]['completed'] += 1

        return [
            {
                'name': project,
                'completed': stats['completed'],
                'total': stats['total']
            }
            for project, stats in sorted(projects.items(), key=lambda x: x[1]['total'], reverse=True)
        ]

    def _get_new_tasks_in_period(self, db_id: str, target_date: date) -> List[Dict]:
        """Gets tasks created in the specified month"""
        start_date = target_date.replace(day=1)
        end_date = (target_date.replace(day=1, month=target_date.month % 12 + 1)
                    if target_date.month < 12
                    else target_date.replace(year=target_date.year + 1, month=1, day=1)) - timedelta(days=1)

        filter_payload = {
            "and": [
                {
                    "property": "Due",
                    "date": {
                        "on_or_after": start_date.isoformat(),
                        "on_or_before": end_date.isoformat()
                    }
                },
                {
                    "timestamp": "last_edited_time",
                    "last_edited_time": {
                        "on_or_after": start_date.isoformat()
                    }
                }
            ]
        }

        return get_db_pages(db_id, {"filter": filter_payload})

    def _get_overdue_tasks(self, db_id: str) -> List[Dict]:
        """Gets tasks that are overdue"""
        filter_payload = {
            "and": [
                {
                    "property": "Due",
                    "date": {
                        "before": date.today().isoformat()
                    }
                },
                {
                    "property": "Done",
                    "checkbox": {
                        "equals": False
                    }
                }
            ]
        }

        return get_db_pages(db_id, {"filter": filter_payload})

    def _create_task_metrics(self, tasks: List[Dict], previous_tasks: List[Dict]) -> Dict:
        """Creates task metrics with comparisons"""
        current_stats = self._calculate_task_completion(tasks)
        previous_stats = self._calculate_task_completion(previous_tasks)

        # Get non-calendar daily tasks
        daily_creation_stats = self._get_daily_task_creation_stats(tasks)
        previous_daily_creation_stats = self._get_daily_task_creation_stats(previous_tasks)

        # Calculate average completion time
        avg_completion = self.calculate_avg_completion_time(tasks)
        prev_avg_completion = self.calculate_avg_completion_time(previous_tasks)

        return {
            'daily_completed': {
                'current': current_stats['completed'],
                'total': current_stats['total'],
                'rate': current_stats['completion_rate'],
                'comparison': self._format_comparison(
                    current_stats['completion_rate'],
                    previous_stats['completion_rate'],
                    'completion rate'
                )
            },
            'non_calendar_tasks': {
                'current': daily_creation_stats['total_created'],
                'comparison': self._format_comparison(
                    daily_creation_stats['total_created'],
                    previous_daily_creation_stats['total_created'],
                    'tasks created'
                )
            },
            'regular_tasks': {
                'completed': current_stats['completed'],
                'total': current_stats['total'],
                'rate': current_stats['completion_rate'],
                'avg_completion_time': avg_completion,
                'completion_time_comparison': self._format_comparison(
                    parse_duration_to_seconds(avg_completion),
                    parse_duration_to_seconds(prev_avg_completion),
                    'completion time',
                    reverse_comparison=True
                )
            }
        }

    def calculate_avg_completion_time(self, tasks: List[Dict]) -> str:
        """Calculates average completion time for tasks with due dates in current month"""
        completion_times = []

        for task in tasks:
            if task['properties'].get('Done', {}).get('checkbox', True):
                created_time = datetime.fromisoformat(task['created_time'].replace('Z', '+00:00'))
                completed_time = datetime.fromisoformat(task['last_edited_time'].replace('Z', '+00:00'))
                completion_time = completed_time - created_time
                completion_times.append(completion_time.total_seconds())

        if completion_times:
            avg_seconds = sum(completion_times) / len(completion_times)
            return seconds_to_hours_minutes(avg_seconds)
        return "N/A"

    def _get_daily_task_creation_stats(self, tasks: List[Dict]) -> Dict:
        """Gets statistics about daily task creation excluding calendar tasks"""
        calendar_tasks = [
            task for task in tasks
            if task['properties'].get('is_calendar', {}).get('formula', {}).get('string') != 'true'
        ]

        return {
            'total_created': len(calendar_tasks)
        }

    def _calculate_avg_completion_time(self, tasks: List[Dict]) -> str:
        """Calculates average completion time for tasks with due dates in current month"""
        completion_times = []

        for task in tasks:
            if task['properties'].get('Done', {}).get('checkbox', True):
                created_time = datetime.fromisoformat(task['created_time'].replace('Z', '+00:00'))
                completed_time = datetime.fromisoformat(task['last_edited_time'].replace('Z', '+00:00'))
                completion_time = completed_time - created_time
                completion_times.append(completion_time.total_seconds())

        if completion_times:
            avg_seconds = sum(completion_times) / len(completion_times)
            return seconds_to_hours_minutes(avg_seconds)
        return "N/A"