from datetime import datetime


class Employee:
    def __init__(self,
                 name,
                 hebrew_names,
                 available_from=None,
                 preferred_home_days=None,
                 specific_home_dates=None,
                 max_consecutive_home_days=7,
                 min_consecutive_home_days=5,
                 preferred_shift_partner=None,
                 is_manager=False,
                 role=None,
                 contact_info=None):
        self.name = name
        self.hebrew_names = [hebrew_names] if isinstance(hebrew_names, str) else hebrew_names
        self.available_from = (
            datetime.strptime(available_from, '%Y-%m-%d').date()
            if available_from else datetime.now().date()
        )
        self.preferred_home_days = preferred_home_days or []
        self.specific_home_dates = [
            datetime.strptime(date, '%Y-%m-%d').date()
            if isinstance(date, str) else date
            for date in (specific_home_dates or [])
        ]
        self.max_consecutive_home_days = max_consecutive_home_days
        self.min_consecutive_home_days = min_consecutive_home_days
        self.preferred_shift_partner = preferred_shift_partner
        self.is_manager = is_manager
        self.role = role
        self.contact_info = contact_info
        self._id = None
        self.shift_dates = []
        self.home_dates = []
        self.total_shifts_days = 0
        self.total_home_days = 0

    def update_date_counts(self):
        self.total_shifts_days = len(self.shift_dates)
        self.total_home_days = len(self.home_dates)

    def to_dict(self):
        return {
            'name': self.name,
            'hebrew_names': self.hebrew_names,
            'available_from': self.available_from.strftime('%Y-%m-%d'),
            'preferred_home_days': self.preferred_home_days,
            'specific_home_dates': [
                date.strftime('%Y-%m-%d') for date in self.specific_home_dates
            ],
            'max_consecutive_home_days': self.max_consecutive_home_days,
            'min_consecutive_home_days': self.min_consecutive_home_days,
            'preferred_shift_partner': self.preferred_shift_partner,
            'is_manager': self.is_manager,
            'role': self.role,
            'contact_info': self.contact_info,
            'shift_dates': [date.strftime('%Y-%m-%d') for date in self.shift_dates],
            'home_dates': [date.strftime('%Y-%m-%d') for date in self.home_dates],
            'total_shifts_days': self.total_shifts_days,
            'total_home_days': self.total_home_days
        }

    def is_available(self, date):
        """
        Check if the employee is available on a specific date.

        :param date: Date to check availability
        :return: Boolean indicating availability
        """
        # Ensure date is a date object
        if isinstance(date, datetime):
            date = date.date()

        # Check if date is before availability start
        if date < self.available_from:
            return False

        # Check if date is in specific home dates
        if date in self.specific_home_dates:
            return False

        # Check preferred home days (if date is a specific day of week)
        if (self.preferred_home_days and
                date.strftime('%A').lower() in
                [day.lower() for day in self.preferred_home_days]):
            return False

        return True
