import requests
from datetime import datetime, timedelta
import pytz
import json
from typing import Dict, List, Tuple
from difflib import SequenceMatcher
from dataclasses import dataclass
from collections import defaultdict


# [Previous imports remain the same...]

class APICategory:
    """Categories of items returned by the Hebcal API"""
    CANDLES = 'candles'
    HAVDALAH = 'havdalah'
    PARASHAT = 'parashat'


class JewishAPIResponse:
    """Fields in the API response"""
    TITLE = 'title'
    HEBREW = 'hebrew'
    DATE = 'date'
    HDATE = 'hdate'
    LINK = 'link'
    CATEGORY = 'category'
    MEMO = 'memo'
    ITEMS = 'items'


class TimeFormat:
    """Time format settings"""
    ISO_FORMAT = '%Y-%m-%d'
    DISPLAY_FORMAT = '%H:%M'
    UTC_SUFFIX = 'Z'
    UTC_REPLACEMENT = '+00:00'


class APIParams:
    """API request parameters"""
    CONFIG = 'cfg'
    CITY = 'city'
    START = 'start'
    END = 'end'

    @classmethod
    def get_params_dict(cls, city: str, start_date: datetime, end_date: datetime) -> Dict:
        """Create parameters dictionary for API request"""
        return {
            cls.CONFIG: 'json',
            cls.CITY: city,
            cls.START: start_date.strftime(TimeFormat.ISO_FORMAT),
            cls.END: end_date.strftime(TimeFormat.ISO_FORMAT)
        }


@dataclass
class CityTimes:
    city: str
    candle_lighting: str
    havdalah: str


class Shabbat:
    def __init__(self):
        self.parasha_name = ""
        self.parasha_hebrew = ""
        self.date = ""
        self.hebrew_date = ""
        self.link = ""
        self.summary = ""
        self.city_times: List[CityTimes] = []

    def __str__(self) -> str:
        cities_info = "\n".join(
            f"  {ct.city}: Candle Lighting: {ct.candle_lighting}, Havdalah: {ct.havdalah}"
            for ct in self.city_times
        )
        return (
            f"Parasha: {self.parasha_hebrew} ({self.parasha_name})\n"
            f"Date: {self.date} ({self.hebrew_date})\n"
            f"Cities:\n{cities_info}\n"
            f"Link: {self.link}\n"
            f"Summary: {self.summary[:200]}..."
        )

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, date_key: str):
        if date_key:
            # Convert string to datetime
            date_obj = datetime.strptime(date_key, '%Y-%m-%d')
            # Subtract one day
            prev_day = date_obj - timedelta(days=1)
            # Convert back to string format
            self._date = prev_day.strftime('%Y-%m-%d')
        else:
            self._date = ""

    def to_dict(self) -> Dict:
        """Convert Shabbat object to dictionary."""
        return {
            JewishAPIResponse.TITLE: self.parasha_name,
            JewishAPIResponse.HEBREW: self.parasha_hebrew,
            JewishAPIResponse.DATE: self.date,
            JewishAPIResponse.HDATE: self.hebrew_date,
            JewishAPIResponse.LINK: self.link,
            'summary': self.summary,
            'cities': [
                {
                    APIParams.CITY: ct.city,
                    'candle_lighting': ct.candle_lighting,
                    'havdalah': ct.havdalah
                }
                for ct in self.city_times
            ]
        }


class JewishCalendarAPI:
    DEFAULT_CITIES = ['Hadera', 'Tel Aviv', 'Haifa']

    def __init__(self, cities: List[str] = None):
        """
        Initialize the Jewish Calendar API.

        Args:
            cities: List of cities to get times for. If None, uses default cities.
        """
        self.hebcal_api_base = "https://www.hebcal.com/shabbat"
        self.cities = cities if cities is not None else self.DEFAULT_CITIES
        self.similarity_threshold = 0.7
        self._current_date = datetime.now()
        self.parasha_summaries = {
            "Bereshit": "God creates the heavens and the earth in six days, and rests on the seventh. Adam and Eve are placed in the Garden of Eden, where they sin by eating from the Tree of Knowledge, leading to their expulsion. The parasha also recounts the first murder when Cain kills his brother Abel, and it ends with the growing wickedness of humanity.",

            "Noach": "God instructs Noah, the only righteous man of his generation, to build an ark to survive the great flood that will destroy the corrupt world. Noah, his family, and the animals are saved, and the floodwaters eventually recede. Afterward, God establishes a covenant with Noah, symbolized by the rainbow, but humanity sins again at the Tower of Babel.",

            "Lech-Lecha": "God commands Abram to leave his homeland and promises to make him the father of a great nation. Abram and Sarai journey to Canaan, where God reaffirms His promise of offspring. Abram rescues his nephew Lot from captivity, and God changes his name to Abraham, sealing the covenant with the commandment of circumcision.",

            "Vayera": "Three angels visit Abraham and announce that Sarah will bear a son, Isaac. God informs Abraham of His plan to destroy Sodom and Gomorrah due to their wickedness, and Abraham pleads for the cities. The parasha concludes with the binding of Isaac, where Abraham's faith is tested as he is commanded to sacrifice his son, but an angel intervenes.",

            "Chayei Sarah": "Sarah dies at the age of 127, and Abraham purchases the Cave of Machpelah as a burial site for her. Abraham sends his servant to find a wife for Isaac, and the servant returns with Rebecca. Abraham dies and is buried next to Sarah by his sons Isaac and Ishmael.",

            "Toldot": "Isaac and Rebecca have twin sons, Esau and Jacob, who struggle even in the womb. Esau sells his birthright to Jacob for a bowl of lentil stew. In his old age, Isaac is tricked into giving his blessing to Jacob instead of Esau, setting the stage for future conflict between the brothers.",

            "Vayetzei": "Jacob flees to his uncle Laban's house to escape Esau’s wrath and dreams of a ladder reaching to heaven. Jacob marries Leah and Rachel, and despite Laban’s deceit, he fathers eleven sons and one daughter. He becomes wealthy and decides to return to Canaan.",

            "Vayishlach": "Jacob prepares to meet Esau after many years apart, fearing Esau’s revenge. He wrestles with an angel and is given the name Israel. Jacob and Esau reconcile, but tragedy strikes when Jacob's daughter Dinah is abducted and violated, leading to the vengeful actions of her brothers Simeon and Levi.",

            "Vayeshev": "Jacob favors Joseph, which causes jealousy among his brothers. Joseph has prophetic dreams that suggest his future dominance, which further alienates him from his brothers. They sell him into slavery, and he ends up in Egypt, where he rises to a position of trust in Potiphar’s house, only to be falsely accused and imprisoned.",

            "Miketz": "Joseph interprets Pharaoh’s dreams, predicting seven years of plenty followed by seven years of famine. Pharaoh appoints Joseph as viceroy of Egypt, and Joseph manages the grain supplies. During the famine, Joseph's brothers come to Egypt to buy food, but they do not recognize him, and he tests them to see if they have changed.",

            "Vayigash": "Judah pleads with Joseph to take Benjamin’s place as a slave, which leads Joseph to reveal his true identity to his brothers. Joseph forgives them and invites the entire family to settle in Egypt. Jacob and his family move to Egypt, and Joseph and his father are reunited after many years.",

            "Vayechi": "Jacob blesses his sons, giving each a prophetic message about their future. He asks to be buried in the Cave of Machpelah in Canaan and passes away at the age of 147. After Jacob’s death, Joseph reassures his brothers that he harbors no grudge and dies in Egypt at the age of 110, requesting that his bones be carried back to the land of Israel.",

            "Shemot": "The Israelites are enslaved in Egypt, and Pharaoh orders the killing of all newborn Hebrew boys. Moses is born and raised in Pharaoh’s house but flees to Midian after killing an Egyptian taskmaster. God appears to Moses in the burning bush and sends him back to Egypt to free the Israelites.",

            "Va'eira": "God commands Moses and Aaron to demand the release of the Israelites from Pharaoh. Pharaoh refuses, and God sends the first seven of the ten plagues upon Egypt. Despite the suffering, Pharaoh’s heart is hardened, and he continues to resist.",

            "Bo": "God brings the final three plagues upon Egypt, culminating in the death of the firstborn. Pharaoh finally agrees to release the Israelites. The Israelites prepare for the Exodus, marking the beginning of the observance of Passover.",

            "Beshalach": "The Israelites leave Egypt, but Pharaoh changes his mind and pursues them. God parts the Red Sea, allowing the Israelites to escape and drowning the Egyptians. In the wilderness, the Israelites complain about a lack of food and water, and God provides manna and water from a rock.",

            "Yitro": "Moses’ father-in-law, Jethro, advises him to delegate leadership responsibilities. The Israelites reach Mount Sinai, where God reveals the Ten Commandments. The people experience an awe-inspiring revelation but are too fearful to hear directly from God and ask Moses to mediate.",

            "Mishpatim": "God gives the Israelites a set of civil and ethical laws to guide their society, including laws about servants, personal injury, and property. The Israelites accept the covenant with God, declaring 'we will do and we will hear.' Moses ascends Mount Sinai to receive the tablets of the law.",

            "Terumah": "God instructs the Israelites to build the Tabernacle, a portable sanctuary for worship. Detailed descriptions are given for the construction of the Ark of the Covenant, the menorah, and the altar. The materials for the Tabernacle are donated by the people.",

            "Tetzaveh": "God gives further instructions regarding the priestly garments that Aaron and his sons are to wear. The priestly garments include the ephod, breastplate, and turban. Instructions for the inauguration of the priests and the daily offerings are also provided.",

            "Ki Tisa": "Moses is instructed to take a census and the Israelites are commanded to contribute to the building of the Tabernacle. While Moses is on Mount Sinai, the people grow impatient and build the Golden Calf, which angers God. Moses intercedes for the people, and God forgives them, renewing the covenant.",

            "Vayakhel": "Moses gathers the people and instructs them on how to build the Tabernacle. The people donate materials, and the artisans, led by Bezalel and Oholiab, construct the various elements of the Tabernacle. The parasha emphasizes the importance of observing the Sabbath, even while building the sanctuary.",

            "Pekudei": "The construction of the Tabernacle is completed, and all its components are brought to Moses. Moses inspects the work and blesses the people. The cloud of God's presence fills the Tabernacle, signifying that God will dwell among the Israelites on their journey.",

            "Vayikra": "God calls to Moses from the Tent of Meeting and gives instructions regarding the various offerings, including burnt offerings, grain offerings, and peace offerings. The laws of atonement for unintentional sins are outlined. The parasha emphasizes the holiness of the sacrificial service.",

            "Tzav": "Further details are provided about the various offerings, including the burnt, grain, sin, and guilt offerings. Aaron and his sons are consecrated as priests, and they begin their service in the Tabernacle. The parasha also discusses the prohibition against consuming blood and fat from sacrifices.",

            "Shemini": "On the eighth day of the Tabernacle’s inauguration, Aaron and his sons begin their priestly duties. Tragedy strikes when two of Aaron's sons, Nadav and Avihu, offer unauthorized fire before God and are consumed by fire. The parasha concludes with the dietary laws, including the animals that are permitted and forbidden to eat.",

            "Tazria": "The laws concerning childbirth and ritual impurity are introduced, detailing how a woman becomes ritually impure after giving birth and how she becomes purified. The parasha also describes the laws of tzara'at, a spiritual affliction that manifests on the skin, clothing, or homes, and how the priest diagnoses and purifies the afflicted.",

            "Metzora": "The process for purifying a person afflicted with tzara'at is detailed, including offerings and rituals performed by the priest. The parasha also addresses how homes afflicted with tzara'at are purified. The laws of bodily discharges and their impact on ritual purity are presented.",

            "Acharei Mot": "After the death of Aaron’s sons, God instructs Moses regarding the Yom Kippur service, which includes the rituals of atonement. The scapegoat ceremony, where one goat is sent into the wilderness carrying the sins of the Israelites, is introduced. The parasha also warns against immoral behaviors, including idolatry and improper sexual relationships.",

            "Kedoshim": "God commands the Israelites to be holy, giving a detailed list of ethical and moral laws. These include respect for parents, honesty in business, love for one's neighbor, and the prohibition against idol worship. The parasha emphasizes justice, equality, and integrity as essential aspects of holiness.",

            "Emor": "The parasha discusses the special rules for the priests, including restrictions on whom they may marry and their responsibilities in the Temple. The laws of the festivals, such as Passover, Shavuot, and Sukkot, are outlined. The parasha also includes the laws of blasphemy and consequences for those who disrespect God’s name.",

            "Behar": "God gives the laws of the Sabbatical and Jubilee years, during which the land must rest, and property is returned to its original owners. These laws emphasize economic fairness and social justice. The parasha also discusses the treatment of servants and the prohibition of charging interest on loans.",

            "Bechukotai": "God promises blessings for obedience to His commandments, including prosperity, peace, and security in the land. However, He also warns of severe punishments for disobedience, such as famine, exile, and the destruction of the land. The parasha concludes with the laws of vows and consecrated offerings.",

            "Bamidbar": "The book of Numbers begins with a census of the Israelite tribes as they prepare to enter the land of Canaan. The parasha describes the organization of the camp, with each tribe having a designated position around the Tabernacle. The Levites are appointed as the tribe responsible for the service of the Tabernacle.",

            "Naso": "The parasha describes the responsibilities of the Levites and details the laws of the Nazirite vow. The priestly blessing is introduced, a three-part blessing that is still recited today. The offerings brought by the leaders of the tribes during the dedication of the Tabernacle are detailed.",

            "Behaalotcha": "God commands Aaron to light the menorah in the Tabernacle. The parasha also includes the laws concerning the Passover offering and the Israelites' journey through the wilderness. Complaints about the lack of meat lead God to provide quail, but also a plague for their ingratitude.",

            "Shelach": "Moses sends twelve spies to scout the land of Canaan, but ten return with a negative report, causing the people to rebel. As a result, God decrees that the Israelites will wander in the desert for forty years until the faithless generation dies out. The parasha also includes the laws of offerings and the commandment to wear tzitzit.",

            "Korach": "Korach leads a rebellion against Moses and Aaron, challenging their leadership. God intervenes, and Korach and his followers are swallowed by the earth. The parasha emphasizes the divine selection of Aaron's descendants for the priesthood and includes laws regarding the responsibilities of the priests and Levites.",

            "Chukat": "The parasha describes the laws of the red heifer, which purifies those who have come into contact with the dead. The Israelites continue their journey through the wilderness, where Miriam and Aaron both die. Moses strikes a rock to provide water, but as a result, he is told he will not enter the Promised Land.",

            "Balak": "Balak, the king of Moab, hires the prophet Balaam to curse the Israelites. However, every time Balaam tries to curse them, he ends up blessing them instead. The parasha concludes with the Israelites sinning with the Moabite women and worshiping Baal Peor, leading to a plague.",

            "Pinchas": "Pinchas is rewarded for stopping a plague by killing an Israelite man and a Midianite woman who were sinning publicly. The parasha includes a new census of the Israelites and the inheritance laws for the daughters of Zelophehad. God instructs Moses to appoint Joshua as his successor.",

            "Matot": "Moses gives instructions regarding vows and oaths, particularly those made by women. The Israelites wage war against the Midianites, and the laws concerning the spoils of war are described. The parasha also discusses the request of the tribes of Reuben and Gad to settle on the eastern side of the Jordan River.",

            "Masei": "The parasha recounts the stages of the Israelites' journey from Egypt to the plains of Moab. God gives instructions for the future division of the land of Canaan among the tribes and establishes cities of refuge for those who commit accidental manslaughter. The parasha concludes with additional inheritance laws concerning women.",

            "Devarim": "Moses begins his farewell address to the Israelites, recounting their journey from Mount Sinai to the present. He reminds the people of their past rebellions and God's guidance. Moses urges the Israelites to follow God's commandments as they prepare to enter the Promised Land.",

            "Va'etchanan": "Moses pleads with God to allow him to enter the Promised Land, but God refuses. Moses continues his address, reminding the Israelites of the importance of obeying God's laws. The parasha includes a repetition of the Ten Commandments and the Shema, emphasizing the centrality of monotheism.",

            "Eikev": "Moses tells the Israelites that their success in the Promised Land depends on their obedience to God. He recounts their past rebellions, including the sin of the Golden Calf, and reminds them of God's mercy. The parasha also emphasizes the blessings that come with following God's commandments.",

            "Re'eh": "Moses sets before the Israelites a choice between blessings for obedience and curses for disobedience. The parasha discusses the laws of idolatry, the dietary laws, and the observance of the festivals. The Israelites are commanded to show generosity and care for the poor.",

            "Shoftim": "Moses outlines the rules for establishing a just society, including the appointment of judges and the conduct of kings. The parasha also discusses the role of prophets, the cities of refuge, and the rules of warfare. The Israelites are reminded to seek justice and fairness in all aspects of life.",

            "Ki Teitzei": "The parasha contains numerous laws governing family life, business ethics, and social justice. These include laws about marriage, divorce, and the treatment of captives. The parasha emphasizes compassion and fairness, particularly in the treatment of the vulnerable members of society.",

            "Ki Tavo": "Moses instructs the Israelites to bring the first fruits of their harvest to the Temple and pronounce their gratitude to God. The parasha includes blessings for obedience and curses for disobedience. Moses urges the Israelites to remain faithful to God as they enter the Promised Land.",

            "Nitzavim": "Moses gathers all the Israelites and renews the covenant with them, emphasizing that it is binding for all generations. He sets before them the choice between life and death, urging them to choose life by following God's commandments. The parasha highlights the importance of repentance and returning to God.",

            "Vayelech": "Moses prepares for his death and instructs the Israelites to remain faithful to God. He writes down the Torah and gives it to the Levites to place in the Ark of the Covenant. Moses also teaches the Israelites a song that will serve as a witness against them if they turn away from God.",

            "Haazinu": "Moses recites a song that summarizes the history of Israel, including their future rebellions and God's mercy. The song warns of the consequences of disobedience but also promises redemption. God tells Moses to ascend Mount Nebo, where he will see the Promised Land before he dies.",

            "Vezot Haberachah": "The final parasha of the Torah, in which Moses blesses each of the tribes of Israel before his death. Moses ascends Mount Nebo, where he views the Promised Land from afar. He dies there, and the Torah concludes with the Israelites preparing to enter the land under Joshua's leadership."
        }
    @property
    def date(self) -> datetime:
        """Get current date being used for calculations."""
        return self._current_date

    @date.setter
    def date(self, new_date: datetime) -> None:
        """Set new date for calculations."""
        self._current_date = new_date

    def set_cities(self, cities: List[str]) -> None:
        """Update the list of cities."""
        self.cities = cities

    def add_city(self, city: str) -> None:
        """Add a new city to the list."""
        if city not in self.cities:
            self.cities.append(city)

    def remove_city(self, city: str) -> None:
        """Remove a city from the list."""
        if city in self.cities:
            self.cities.remove(city)

    def get_next_shabbat_date(self) -> datetime:
        """Get the next Shabbat date from current date."""
        days_ahead = 5 - self._current_date.weekday()  # Friday is 5
        if days_ahead <= 0:
            days_ahead += 7
        return self._current_date + timedelta(days=days_ahead)

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings."""
        str1 = str1.lower().replace('parashat ', '').replace('-', ' ').strip()
        str2 = str2.lower().replace('parashat ', '').replace('-', ' ').strip()
        return SequenceMatcher(None, str1, str2).ratio()

    def _normalize_parasha_name(self, name: str) -> str:
        """Normalize parasha name to match summary dictionary keys."""
        best_match = None
        highest_similarity = self.similarity_threshold

        for known_parasha in self.parasha_summaries.keys():
            similarity = self._calculate_similarity(name, known_parasha)
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = known_parasha

        return best_match if best_match else name

    def _get_parasha_summary(self, parasha_name: str) -> str:
        """Get parasha summary handling different name variations."""
        normalized_name = self._normalize_parasha_name(parasha_name)
        return self.parasha_summaries.get(normalized_name, "Summary not available")

    def get_shabbat_times(self) -> List[Shabbat]:
        """Get Shabbat times for the configured cities using current date."""
        shabbat_dict = {}
        end_date = self._current_date + timedelta(days=7)

        for city in self.cities:
            params = APIParams.get_params_dict(city, self._current_date, end_date)

            response = requests.get(self.hebcal_api_base, params=params)
            response.raise_for_status()
            data = response.json()

            if JewishAPIResponse.ITEMS not in data:
                continue

            # Group items by category
            items_by_category = defaultdict(list)
            for item in data[JewishAPIResponse.ITEMS]:
                items_by_category[item[JewishAPIResponse.CATEGORY]].append(item)

            # Process each parashat
            for parashat in items_by_category[APICategory.PARASHAT]:
                date_key = parashat[JewishAPIResponse.DATE]

                if date_key not in shabbat_dict:
                    shabbat = Shabbat()
                    shabbat.parasha_name = parashat.get(
                        JewishAPIResponse.TITLE, ''
                    ).replace('Parashat ', '')
                    shabbat.parasha_hebrew = parashat.get(JewishAPIResponse.HEBREW, '')
                    shabbat.date = date_key
                    shabbat.hebrew_date = parashat.get(JewishAPIResponse.HDATE, '')
                    shabbat.link = parashat.get(JewishAPIResponse.LINK, '')
                    shabbat.summary = self._get_parasha_summary(shabbat.parasha_name)
                    shabbat_dict[date_key] = shabbat

                # Find matching candle lighting and havdalah times
                candle_time = next(
                    (format_time(item[JewishAPIResponse.DATE])
                     for item in items_by_category[APICategory.CANDLES]
                     if item.get(JewishAPIResponse.MEMO, '') ==
                     parashat.get(JewishAPIResponse.TITLE, '')),
                    "Time not available"
                )

                havdalah_time = next(
                    (format_time(item[JewishAPIResponse.DATE])
                     for item in items_by_category[APICategory.HAVDALAH]
                     if parashat.get(JewishAPIResponse.DATE, '') in
                     item.get(JewishAPIResponse.DATE, '')),
                    "Time not available"
                )

                shabbat_dict[date_key].city_times.append(
                    CityTimes(city=city, candle_lighting=candle_time, havdalah=havdalah_time)
                )

        return list(shabbat_dict.values())


def format_time(dt_str: str) -> str:
    """Format datetime string to readable time."""
    try:
        dt = datetime.fromisoformat(
            dt_str.replace(
                TimeFormat.UTC_SUFFIX,
                TimeFormat.UTC_REPLACEMENT
            )
        )
        israel_tz = pytz.timezone('Asia/Jerusalem')
        dt = dt.astimezone(israel_tz)
        return dt.strftime(TimeFormat.DISPLAY_FORMAT)
    except Exception as e:
        return "Time not available"


def main():
    # Example usage with custom cities
    api = JewishCalendarAPI()

    print("Shabbat Times and Parasha Information for the Upcoming Week")
    print("=" * 70)

    try:
        # Get times using internal date management
        shabbat_list = api.get_shabbat_times()

        # Print information
        for shabbat in shabbat_list:
            print(f"\n{shabbat}")
            print("-" * 70)

        # Example of adding a new city
        api.add_city('Eilat')

        # # Example of setting a specific date
        # next_week = datetime.now() + timedelta(days=7)
        # api.date = next_week
        #
        # # Get times for next week
        # next_week_shabbat = api.get_shabbat_times()

    except Exception as e:
        print(f"Error getting times: {str(e)}")

    return shabbat_list


# if __name__ == "__main__":
#     main()
