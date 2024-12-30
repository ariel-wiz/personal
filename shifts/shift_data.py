from shifts.employee import Employee, DateRange

EMPLOYEES = [
    Employee(
        name='Maslow',
        hebrew_names='מסלו',
        available_from='2024-12-26',
        is_manager=True,
        is_shomer_shabat=True
    ),
    Employee(
        name='Madmoni',
        hebrew_names='מדמוני',
        available_from='2024-12-26',
        is_manager=True,
    ),
    Employee(
        name='Rosen',
        hebrew_names='רוזן',
        available_from='2024-12-26',
    ),
    Employee(
        name='Aghion',
        hebrew_names='אגיון',
        available_from='2024-12-26',
        wish_day_at_home=[DateRange(date_start="05/01", date_end="09/01"),
                          DateRange(date_start="19/01", date_end="25/01"),
                          DateRange(date_start="09/02", date_end="13/02")]

    ),
    Employee(
        name='Sivan',
        hebrew_names='סיוון',
        available_from='2024-12-26',
        must_day_at_home=[DateRange(date_start="12/01", date_end="16/01")]

    ),
    Employee(
        name='Tobiana',
        hebrew_names='טוביאנה',
        available_from='2024-12-26',
        preferred_shift_partner='Pinhas',
    ),
    Employee(
        name='Turjeman',
        hebrew_names=['תורגמן', "תורג'מן"],
        available_from='2024-12-26',
        min_consecutive_home_days=7,
    ),
    Employee(
        name='Oz',
        hebrew_names='עוז',
        available_from='2024-12-26',
        is_shomer_shabat=True
    ),
    Employee(
        name='Aharoni',
        hebrew_names='אהרוני',
        available_from='2024-12-26',
        min_consecutive_home_days=1,
    ),
    Employee(
        name='Pavel',
        hebrew_names='פבל',
        available_from='2024-12-26',
        must_day_at_home=[DateRange(date_start="10/01", date_end="10/01"),
                          DateRange(date_start="15/01", date_end="15/01")]
    ),
    Employee(
        name='Rahamim',
        hebrew_names='רחמים',
        available_from='2025-01-15',
        is_shomer_shabat=True
    ),
    Employee(
        name='Pinhas',
        hebrew_names='פנחס',
        available_from='2024-12-26',
        is_shomer_shabat=True
    ),
    Employee(
        name='Elior',
        hebrew_names='אליאור',
        available_from='2024-12-26',
        is_shomer_shabat=True,
        must_day_at_home=[DateRange(date_start="09/01", date_end="15/02")]
    ),
    Employee(
        name='Shushan',
        hebrew_names='שושן',
        available_from='2025-01-03',
    ),
    Employee(
        name='Ron',
        hebrew_names='רון',
        available_from='2024-12-26',
    )
]
