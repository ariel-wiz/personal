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
        self.parasha_summaries_english = {
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
        self.parasha_summaries = {
            "bereshit": "פרשת בראשית עוסקת בבריאת העולם על ידי אלוהים בשישה ימים והשבת כיום מנוחה. היא מתארת את בריאת האדם הראשון, אדם וחווה, ואת חטא עץ הדעת שגורם לגירושם מגן עדן. בהמשך מובא סיפור קין והבל, בו קין רוצח את אחיו. הפרשה מסתיימת בתיאור השחתת האנושות והחלטת האל להביא מבול על הארץ. נח מוצא חן בעיני ה' ומקבל את המשימה לבנות תיבה.",
            "noach": "פרשת נח מתארת את בניית התיבה על ידי נח ומשפחתו, והמבול שהשמיד את כל היצורים על פני האדמה. לאחר מכן, אלוהים כורת ברית עם נח ומבטיח שלא יביא מבול נוסף, כשהקשת בענן משמשת כאות לברית זו. נח ומשפחתו יוצאים מהתיבה ומתחילים ליישב את העולם מחדש. הפרשה כוללת את סיפור מגדל בבל, בו בני האדם ניסו לעלות לשמים, והאל בלל את שפתם. הפרשה מסתיימת בציון צאצאיו של נח ותולדות משפחותיהם.",
            "lech-lecha": "פרשת לך לך מתארת את צו ה' לאברהם לעזוב את ארצו וללכת אל ארץ כנען. ה' מבטיח לאברהם שיהיה לגוי גדול ושהארץ תהיה ירושה לצאצאיו. הפרשה עוסקת במסעו של אברהם וביחסיו עם לוט, אחיינו, ובמלחמתו במלכים לשחרור לוט. כמו כן, נחתמת ברית בין הבתרים שבה ה' מבטיח את הארץ לצאצאי אברהם. הפרשה מסתיימת בציווי ברית המילה כחותם לברית עם אלוהים.",
            "vayera": "פרשת וירא כוללת את ביקור שלושת המלאכים אצל אברהם והבשורה על הולדת יצחק. הפרשה מתארת את סיפור הפיכת סדום ועמורה ואת הצלת לוט ומשפחתו. אברהם נושא ונותן עם ה' על גורל הערים החוטאות. בהמשך, נולד יצחק ונערכת עקדת יצחק, בה נבחנת נאמנותו של אברהם לה'. הפרשה מסתיימת בתיאור משפחת נחור, אחי אברהם.",
            "chayei sarah": "פרשת חיי שרה פותחת במות שרה ובקניית מערת המכפלה על ידי אברהם לקבורתה. אברהם שולח את עבדו לחפש אישה ליצחק, ומסעו מוביל אותו לרבקה. הפרשה מתארת את פגישתו של אליעזר עם רבקה ואת הסכמת משפחתה לנישואין. יצחק ורבקה נפגשים ומתחתנים, ונוצר חיבור עמוק ביניהם. הפרשה מסתיימת במותו של אברהם ובקבורתו לצד שרה במערת המכפלה.",
            "toldot": "פרשת תולדות מתארת את לידת עשו ויעקב, התאומים של יצחק ורבקה, ואת מערכת היחסים המורכבת ביניהם. עשו מוכר את הבכורה ליעקב תמורת נזיד עדשים. בהמשך, יעקב מתחפש לעשו כדי לקבל את הברכה מאביו יצחק. עשו כועס ורוצה להרוג את יעקב, ולכן רבקה שולחת את יעקב להימלט לחרן. הפרשה מסתיימת ביציאתו של יעקב למסעו והכנתו לפגישה עם לבן.",
            "vayetze": "פרשת ויצא מתארת את מסעו של יעקב לחרן ואת חלום הסולם, בו מלאכי אלוהים עולים ויורדים. יעקב פוגש את רחל ליד הבאר ומתאהב בה, אך לבן מרמה אותו ומשיא לו קודם את לאה. יעקב עובד שבע שנים נוספות כדי לשאת את רחל, ונולדים לו שנים עשר ילדים עם רחל, לאה, ובנות שפחותיהן. בהמשך, יעקב מחליט לחזור לארץ כנען, תוך שהוא מתמודד עם לבן שמנסה לעצור אותו. הפרשה מסתיימת בברית בין יעקב ללבן וביציאתו של יעקב לדרכו.",
            "vayishlach": "פרשת וישלח מספרת על חזרתו של יעקב לארץ כנען ועל פגישתו עם עשו. יעקב שולח מתנות לעשו כדי לפייס אותו, ומתכונן לעימות אפשרי. בלילה, הוא נאבק עם מלאך ונקרא בשם ישראל. הפגישה עם עשו מסתיימת בשלום, והשניים נפרדים. הפרשה מסתיימת בסיפור דינה ובני שכם, וכן ברשימת תולדות עשו.",
            "vayeshev": "פרשת וישב מתארת את יחסו של יעקב לבניו, כאשר יוסף זוכה לאהבה מיוחדת ושנאה מצד אחיו. האחים זוממים להרוג את יוסף, אך במקום זאת מוכרים אותו לישמעאלים. יוסף מגיע למצרים ומתחיל לעבוד בבית פוטיפר, אך מסתבך בעקבות האשמות אשת פוטיפר. בינתיים, מסופר על מעשיו של יהודה עם תמר. הפרשה מסתיימת ביוסף בכלא ובחלומותיהם של שר המשקים ושר האופים.",
            "miketz": "פרשת מקץ ממשיכה את סיפורו של יוסף במצרים, שם הוא פותר את חלומות פרעה על שבע שנות השפע ושבע שנות הרעב. יוסף מתמנה למשנה למלך מצרים ואחראי על ניהול המשבר. אחי יוסף מגיעים למצרים לקנות אוכל, אך אינם מזהים אותו. יוסף בוחן אותם ומאשים אותם בריגול, ודורש להביא את בנימין כהוכחה. הפרשה מסתיימת בהשבת בנימין למצרים ובתחושת האחים בצרה.",
            "vayigash": "פרשת ויגש עוסקת במפגש הדרמטי בין יוסף לאחיו, כשיהודה ניגש אליו ומתחנן על חיי בנימין. יוסף חושף את זהותו, והאחים מתפייסים. יעקב ובניו עוברים למצרים ומתיישבים בארץ גושן. פרעה מברך את יעקב, ויוסף מספק אוכל למשפחתו ולמצרים בזמן הרעב. הפרשה מסתיימת ברשימת צאצאי יעקב שהגיעו למצרים.",
            "vayechi": "פרשת ויחי מתארת את ימיו האחרונים של יעקב במצרים ואת ברכותיו לבניו. יעקב מברך את מנשה ואפרים, בניו של יוסף, ומעניק להם מעמד שווה לשאר השבטים. לאחר מותו, יעקב נקבר במערת המכפלה. האחים חוששים מנקמת יוסף, אך הוא מבטיח שלא יפגע בהם. הפרשה והספר מסתיימים במות יוסף ובהבטחתו להעלות את עצמותיו לארץ ישראל.",
            "shemot": "פרשת שמות פותחת בסיפור השעבוד של בני ישראל במצרים והתרבותם. פרעה גוזר על הבנים להיזרק ליאור, ומשה ניצל ונאסף לבית פרעה. משה בורח למדיין לאחר שהרג מצרי, ושם מתגלה לו אלוהים בסנה הבוער. ה' מצווה את משה להוציא את בני ישראל ממצרים. משה ואהרון מתחילים את שליחותם מול פרעה, אך הוא מקשה את עול העבדים.",
            "vaera": "פרשת וארא מתארת את תחילת עשר המכות ששלח אלוהים למצרים דרך משה ואהרון. הפרשה כוללת את מכות דם, צפרדע, כינים, וערוב. פרעה מסרב לשחרר את בני ישראל למרות הסבל שנגרם לעמו. אלוהים מחזק את לב פרעה כדי להראות את גדולתו. המכות נמשכות ומחזקות את אמונת העם באלוהים.",
            "bo": "פרשת בא מתארת את שלוש המכות האחרונות: ארבה, חושך, ומכת בכורות. בני ישראל מקבלים מצווה להכין את קורבן הפסח ולהימנע מחמץ. בליל מכת בכורות, פרעה נכנע ומשחרר את העם. בני ישראל יוצאים ממצרים בחיפזון ומתחילים את מסע הגאולה. הפרשה מסתיימת בציווי על חג הפסח לדורות.",
            "beshalach": "פרשת בשלח מתארת את יציאת בני ישראל ממצרים ואת קריעת ים סוף. פרעה רודף אחריהם, אך טובע עם צבאו בים. בני ישראל שרים את שירת הים לאות הודיה לאלוהים. הם מתחילים את מסעם במדבר ומתמודדים עם צמא ורעב. אלוהים מספק להם מן ומים, והפרשה מסתיימת במלחמת עמלק.",
            "yitro": "פרשת יתרו עוסקת בביקורו של יתרו, חותן משה, ובהצעתו להקים מערכת שיפוט לייעול ההנהגה. בני ישראל מגיעים להר סיני ומתקדשים לקבלת התורה. אלוהים נותן למשה את עשרת הדיברות בנוכחות העם. מעמד הר סיני מלווה בקולות וברקים שמחזקים את אמונת העם. הפרשה מסתיימת בציווי על בניית מזבח.",
            "mishpatim": "פרשת משפטים כוללת חוקים ומשפטים רבים הנוגעים לחיי היום-יום. היא עוסקת בדינים שבין אדם לחברו, כמו עבדות, גניבה, ופיצויים. כמו כן, מובאות מצוות הקשורות לעבודת האל והחגים. בני ישראל מתחייבים לשמור את דברי התורה. הפרשה מסתיימת בתיאור כריתת הברית בין העם לאלוהים.",
            "terumah": "פרשת תרומה עוסקת בציווי על בניית המשכן, מקום לשכינת האל בקרב בני ישראל. ה' מצווה על העם לתרום חומרים למשכן ולכליו. מתוארת תוכנית בניית הארון, המנורה, והשלחן. המשכן מסמל את הקשר הישיר בין אלוהים לעם. הפרשה מסתיימת בפרטים נוספים על מבנה המשכן.",
            "tetzaveh": "פרשת תצוה עוסקת בציווי על הכנת בגדי הכהונה עבור אהרון ובניו. מתוארים בגדי הכהן הגדול, כולל החושן והאפוד. הפרשה עוסקת גם במצוות הקטורת ובתיאור הקרבת הקורבנות במשכן. אהרון ובניו מקבלים את הכשרתם לכהונה. הפרשה מסתיימת בציווי על מזבח הזהב.",
            "ki tisa": "פרשת כי תשא עוסקת במצוות מחצית השקל למימון המשכן ושמירת קדושתו. הפרשה מתארת את חטא העגל, בו בני ישראל עושים עגל זהב בזמן שמשה בהר. משה שובר את לוחות הברית בעקבות החטא ומתפלל לה' שיסלח לעם. ה' מצווה את משה לעלות שוב להר סיני ומעניק לו לוחות חדשים. הפרשה מסתיימת בציווי על שמירת שבת ובתיאור קרינת פני משה.",
            "vayakhel": "פרשת ויקהל עוסקת בהקמת המשכן ובתיאור מלאכתם של בצלאל ואהליאב. משה אוסף את בני ישראל ומצווה אותם לשמור את השבת. העם מביא תרומות לבניית המשכן וכליו בשפע רב. מתוארים בפירוט מבנה המשכן, היריעות, והכלים הקדושים. הפרשה מדגישה את שיתוף הפעולה של כל העם במלאכה.",
            "pekudei": "פרשת פקודי מסכמת את בניית המשכן וכליו בפירוט מדוקדק. משה בודק את כל התרומות ואת העבודה, ומברך את בני ישראל על נאמנותם. המשכן מוקם ומשוח, וה' שוכן בתוכו. הענן מכסה את המשכן ומדריך את מסע העם במדבר. הפרשה מסיימת את ספר שמות בתיאור התגלות ה' במשכן.",
            "vayikra": "פרשת ויקרא פותחת את ספר ויקרא ומתארת את קרבנות העולה, המנחה, והשלמים. הקרבנות מובאים ככפרה על חטאים או כתודה לאלוהים. מתוארת חשיבות הכוונה בעת הקרבת הקורבן. הפרשה מדגישה את התפקיד המרכזי של הכהנים בקיום הפולחן במשכן. היא מסכמת את העקרונות לעבודת הקורבנות בטהרה וקדושה.",
            "tzav": "פרשת צו מתארת את סדר הקרבת הקרבנות והדינים הקשורים אליהם. הכהנים מקבלים הוראות מדויקות על הדלקת המזבח ושמירת האש. מתוארת חנוכת אהרון ובניו לתפקיד הכהונה. הפרשה מדגישה את חשיבות הקדושה והדיוק בעבודת הקורבנות. היא מסתיימת בהכנות להשראת השכינה במשכן.",
            "shmini": "פרשת שמיני מתארת את היום השמיני לחנוכת המשכן ואת הקרבת הקרבנות על ידי אהרון ובניו. בני אהרון, נדב ואביהוא, מקריבים אש זרה ונענשים במותם. הפרשה מתארת את דיני הכשרות וההבחנה בין בעלי חיים טהורים לטמאים. העם לומד את חשיבות שמירת המצוות בהקפדה. היא מסתיימת בציווי על קדושת העם כמשקף את קדושת האל.",
            "tazria": "פרשת תזריע עוסקת בדיני טומאה וטהרה הקשורים ללידה ולנגעי עור. מתוארת דרך טהרת היולדת לאחר הלידה. נגעי צרעת בגוף מתוארים בפרטי פרטים, והכהן הוא הקובע את טומאת האדם. הפרשה מדגישה את הצורך בהסגר ובבדיקה מחודשת. היא מסיימת בהנחיות לטיהור לאחר ההחלמה.",
            "metzora": "פרשת מצורע ממשיכה לתאר את דיני הצרעת והטיהור ממנה. מתוארת דרך הטהרה של המצורע, הכוללת הקרבת קרבנות ושחרור ציפור. הפרשה עוסקת גם בנגעי צרעת בבגדים ובבתים. העם לומד את חשיבות השמירה על קדושת המחנה. היא מסתיימת בהנחיות לטהרה לפני חזרה לחיי החברה.",
            "acharei mot": "פרשת אחרי מות עוסקת בעבודת יום הכיפורים ובתפקיד הכהן הגדול לכפר על עם ישראל. מתוארת כניסתו של הכהן הגדול לקודש הקודשים פעם בשנה. הפרשה כוללת איסורים על הקרבת קורבנות מחוץ למשכן. ניתנות מצוות הקשורות לטהרת העם ולשמירה על חוקי קדושה. היא מסתיימת בציווי להתרחק מתועבות עמי הארץ.",
            "kedoshim": "פרשת קדושים מדגישה את הציווי להיות קדושים כמו האל. היא כוללת מצוות רבות בין אדם לחברו ובין אדם למקום, כמו שמירת שבת וכיבוד הורים. מתוארים עקרונות של צדק חברתי, איסור גניבה, ואיסור רכילות. הפרשה מדגישה את חשיבות האהבה לזולת במצווה 'ואהבת לרעך כמוך'. היא מסיימת בציוויים לשמירת טהרה ואיסור תועבות.",
            "emor": "פרשת אמור עוסקת בדינים הקשורים לכהנים ולמועדי ישראל. הכהנים מחויבים לשמור על טהרתם ואסורים במגע עם טומאה. מתוארים המועדים והשבתות, כולל חגי הפסח, שבועות, סוכות ויום הכיפורים. הפרשה מתארת את מצוות הדלקת המנורה ולחם הפנים במשכן. היא מסתיימת בפרשת המקלל ועונשו.",
            "behar": "פרשת בהר עוסקת במצוות השמיטה והיובל בארץ ישראל. מתוארים דינים לשמירת השבתת האדמה אחת לשבע שנים. שנת היובל מכריזה על חופש עבדים והחזרת קרקעות לבעליהן. הפרשה מדגישה את הציווי להיזהר מדיכוי כלכלי וחברתי. היא מסתיימת בציווי על שמירת הברית עם ה'.",
            "bechukotai": "פרשת בחוקותי מתארת את הברכות שיבואו על שמירת המצוות והקללות על עזיבתן. הברכות כוללות שלום, פרנסה, ונוכחות השכינה בקרב העם. הקללות מתארות עונשים חמורים כמו רעב וגלות. מתוארת חשיבות שמירת הברית בין ה' לבני ישראל. הפרשה מסיימת את ספר ויקרא במצוות הערכת נדרים.",
            "bamidbar": "פרשת במדבר פותחת את ספר במדבר ומונה את שבטי ישראל ואת סדר המחנות במדבר. מתוארים תפקידיהם של הלויים, המשמשים בעבודת המשכן. העם לומד על חשיבות הסדר והמשמעת במחנה. ה' מצווה את משה על מניין העם וארגון מסעותיהם. הפרשה מסתיימת בציווי על הלויים לשמור על קדושת המשכן.",
            "nasso": "פרשת נשא מתארת את תפקידי בני גרשון, קהת, ומררי בנשיאת כלי המשכן. מובאת פרשת סוטה למי שנחשדה בבגידה בבעלה. מתוארת מצוות נזיר והברכה המיוחדת של הכהנים לעם ישראל. נשיאי השבטים מביאים מתנות לחנוכת המשכן. הפרשה מדגישה את חשיבות השותפות בקיום המצוות.",
            "behaalotecha": "פרשת בהעלותך מתארת את ציווי הדלקת המנורה במשכן ותפקידי הלויים בעבודת הקודש. העם מתחיל את מסעיו במדבר, ומובא סיפור תלונת העם על המן. משה מבקש עזרה בהנהגת העם, ואלוהים ממנה שבעים זקנים. סיפור מרים המדברת במשה מסתיים בעונשה בצרעת. הפרשה מדגישה את חשיבות האמונה והצניעות.",
            "shlach": "פרשת שלח עוסקת בשליחת המרגלים לתור את ארץ כנען ודיווחם על תושבי הארץ. העם נבהל ומתרעם על משה ועל אהרון. אלוהים גוזר על דור המדבר למות במדבר ולא להיכנס לארץ. מובאות מצוות הקשורות לקורבנות ולציצית. הפרשה מדגישה את הצורך באמונה ובציות לה'.",
            "korach": "פרשת קורח מתארת את מרד קורח ועדתו נגד מנהיגות משה ואהרון. האדמה פותחת את פיה ובולעת את המורדים. ה' מאשר את בחירת אהרון באמצעות פריחת מטהו. הפרשה כוללת מצוות נוספות על הכהונה והלווייה. היא מסיימת בחיזוק הנהגת משה ואהרון.",
            "chukat": "פרשת חוקת עוסקת בפרה אדומה ובטהרת הטמאים למת. מתוארים מות מרים והכאת משה בסלע במקום לדבר אליו. העם ממשיך להתלונן על תנאי המדבר, ואלוהים שולח נחשים שרפים. משה מצווה להכין נחש נחושת שמרפא את הנפגעים. הפרשה מסתיימת בתיאור מלחמות ישראל בעמלק ובסיחון ועוג.",
            "balak": "פרשת בלק מספרת על ניסיונותיו של בלק, מלך מואב, לשכור את בלעם לקלל את ישראל. בלעם מנסה לקלל אך מברך את העם במקומו, לפי רצון ה'. חמורו של בלעם מדבר ומראה את כוחו של ה'. בלעם מציין את ייחודו של ישראל כעם הנבחר. הפרשה מסתיימת בתיאור חטא בעל פעור ועונשו.",
            "pinchas": "פרשת פינחס מתארת את תגובתו של פינחס לחטא בעל פעור, שמקנה לו ברית שלום מה'. מובאת חלוקת הארץ לשבטים על פי גורל. הפרשה עוסקת במצוות קורבנות המועדים השונים. מובא סיפור בקשת בנות צלפחד לנחלה, ואלוהים מקבל את בקשתן. משה מעביר את ההנהגה ליהושע לפי ציווי ה'.",
            "matot": "פרשת מטות עוסקת בדיני נדרים והבטחות בין אדם למקום. מתוארת מלחמת ישראל במדין ונקמתם על חטא בעל פעור. העם מחלק את השלל לפי ציווי ה'. שבטי ראובן וגד מבקשים נחלה בעבר הירדן המזרחי, ומשה מתנה זאת במילוי חובותיהם הצבאיות. הפרשה מדגישה את מחויבות העם לשמירת דבר ה'.",
            "masei": "פרשת מסעי מסכמת את מסעות בני ישראל במדבר, מתחילת יציאתם ממצרים ועד לערבות מואב. ה' מצווה על ירושת הארץ וחלוקתה בגורל. מתוארים גבולות הארץ ונקבעות ערי מקלט לרוצחים בשגגה. מובאות הוראות נוספות לשמירת קדושת הנחלות. הפרשה מסיימת את ספר במדבר בחיזוק הברית עם ה'.",
            "devarim": "פרשת דברים פותחת את ספר דברים, בו משה נואם לעם לפני כניסתם לארץ ישראל. משה מזכיר לעם את חטאי העבר, כולל חטא המרגלים. הוא מסביר את חשיבות הציות לחוקי ה' ואת האמונה בבורא. משה מתאר את ניצחונות העם במלחמות נגד סיחון ועוג. הפרשה מדגישה את הכנת העם לכניסה לארץ.",
            "vaetchanan": "פרשת ואתחנן כוללת את תפילתו של משה להיכנס לארץ ואת תשובת ה' שמסרב לכך. מובא חידוש עשרת הדיברות ואמירת שמע ישראל. משה מזכיר לעם את חשיבות שמירת החוקים והמצוות. הוא מזהיר מפני עבודה זרה ומדגיש את יחודיותם כעם נבחר. הפרשה מדגישה את הברית הנצחית בין ה' לישראל.",
            "ekev": "פרשת עקב מדגישה את הברכה שתבוא על שמירת המצוות והחוקים. משה מזכיר לעם את ניסי ה' במדבר ואת חטא העגל. הוא קורא לעם לאהוב את ה' ולשמור את מצוותיו. הפרשה מתארת את עושר הארץ ומבטיחה פרנסה ושפע לשומרי הברית. היא מסתיימת בציווי על נאמנות מוחלטת לה'.",
            "reeh": "פרשת ראה עוסקת בברכה ובקללה המותנות בציות למצוות ה'. מובאות הנחיות להשמדת עבודה זרה ולבחירת מקום פולחן מרכזי. הפרשה מפרטת דינים הקשורים לכשרות, מעשרות, וחגי ישראל. משה מציין את חשיבות הנתינה לצדקה והדאגה לעניים. היא מדגישה את ערכי הצדק והאמונה באלוהים.",
            "shoftim": "פרשת שופטים עוסקת במינוי שופטים ושוטרים לשמירת הצדק. מובאות הנחיות על דיני המלך ותפקידיו בעתיד. הפרשה כוללת דינים על עדים, עיר מקלט, ומלחמה הוגנת. משה מצווה על עם ישראל למגר עבודה זרה ולהבטיח מנהיגות מוסרית. היא מדגישה את חשיבות הצדק החברתי והציות לחוקי התורה.",
            "ki_teitzei": "פרשת כי תצא מכילה מצוות רבות הנוגעות לחיי היומיום של עם ישראל. מובאים דינים הקשורים למלחמה, נישואים, ויחסים חברתיים. הפרשה עוסקת בשמירה על ערכי כבוד האדם וקדושת החיים. היא מדגישה את חשיבות הצדקה והדאגה לחלשים בחברה. הפרשה כוללת מצוות השבת אבידה ושכר שכיר.",
            "ki_tavo": "פרשת כי תבוא מתארת את מצוות הביכורים וברכת ה' על הארץ. מובאת ברכת הברכות והקללות על שמירת המצוות או עזיבתן. משה מזכיר לעם את ניסי ה' במדבר ואת הברית הנצחית עם אלוהים. העם מתבקש להכריז על אמונתו ולבחור בחיים ובברכה. הפרשה מדגישה את אחריות העם לשמור על התורה בארץ המובטחת.",
            "nitzavim": "פרשת ניצבים מתארת את הברית המחודשת בין ה' לעם ישראל לפני כניסתם לארץ. משה מדגיש את אחריות כל יחיד בעם לשמור על המצוות. מובאת הבחירה בין חיים למוות, ברכה וקללה. ה' מבטיח תשובה וגאולה לעם שישוב אליו בלב שלם. הפרשה מדגישה את הנצחיות והאוניברסליות של הברית.",
            "vayelech": "פרשת וילך מתארת את יום מותו הקרב של משה ואת הכנתו להעברת ההנהגה ליהושע. משה כותב את התורה ומצווה על קריאתה במעמד הקהל. ה' מצווה את משה על שירת האזהרה לעם ישראל. משה מזהיר את העם מפני התרחקות מה'. הפרשה מדגישה את נוכחות ה' במנהיגות החדשה של יהושע.",
            "haazinu": "פרשת האזינו כוללת את שירת משה, המתארת את נאמנות ה' לעמו. השירה מזהירה מפני עזיבת הברית ותוצאותיה. משה מדגיש את חסדי ה' לאורך הדורות ואת חשיבות האמונה בו. ה' מצווה את משה לעלות להר נבו לראות את הארץ. הפרשה מדגישה את הסיום הקרב של הנהגת משה.",
            "vezot_habracha": "פרשת וזאת הברכה מסיימת את התורה בברכת משה לשבטים לפני מותו. משה מברך כל שבט ומדגיש את תפקידו הייחודי. הוא מתאר את גדולתו של ה' ואת אהבתו לעמו. משה עולה להר נבו ורואה את הארץ לפני פטירתו. התורה מסתיימת בתיאור מות משה, גדולתו, וייחודיותו כמנהיג."
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
