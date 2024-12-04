
from typing import Dict, Any, List

from common import capitalize_text_or_list
from crossfit.crossfit_variables import  NEW_EXERCISES
from logger import logger
from notion_py.helpers.notion_children_blocks import generate_children_block_for_crossfit_exercise
from notion_py.helpers.notion_common import get_db_pages, create_page_with_db_dict, \
    create_page_with_db_dict_and_children_block, generate_icon_url

from notion_py.notion_globals import NotionPropertyType, IconType, IconColor

expertise_map = {
    1: "BEGINNER",  # Basic movements, no technical complexity
    2: "INTERMEDIATE",  # Some technical elements but achievable with practice
    3: "ADVANCED",  # Complex movements requiring consistent practice
    4: "EXPERT",  # High technical demand and prerequisite strength
    5: "ELITE"  # Olympic lifting variations and complex gymnastic movements
}


class CrossfitExercise:
    def __init__(self, name: str, data: Dict[str, Any]):
        self.name = name
        self.tips = data.get('tips', [])
        self.equipment = capitalize_text_or_list(data.get('equipment', []))
        self.expertise = data.get('expertise', 1)
        self.expertise_level = self.get_expertise_level()
        self.demo_url = data.get('demo_url', '')
        self.crossfit_url = data.get('crossfit_url', '')
        self.body_part = capitalize_text_or_list(data.get('body_part', []))
        self.description = data.get('description', [])

    def __str__(self) -> str:
        equipment_str = ", ".join(self.equipment) if self.equipment else "No equipment"
        body_parts = ", ".join(self.body_part) if self.body_part else "Full body"
        return f"{self.name} ({self.expertise_level}) - Equipment: {equipment_str} - Target: {body_parts}"

    def __repr__(self) -> str:
        return f"CrossfitExercise(name='{self.name}', expertise={self.expertise}, equipment={self.equipment}, " \
               f"body_part={self.body_part}, tips={len(self.tips)}, description={len(self.description)} steps, " \
               f"demo_url='{self.demo_url}')"

    def get_expertise_level(self) -> str:
        if self.expertise not in expertise_map:
            raise ValueError(f"Level must be between 1-5, got {self.expertise}")

        return capitalize_text_or_list(expertise_map[self.expertise])

    def payload(self) -> Dict:
        """Creates a Notion database payload for a CrossFit exercise"""
        return {
            "Name": self.name,
            "Equipment": self.equipment,
            "Expertise": self.expertise_level,
            "Video": self.demo_url,
            "Link": self.crossfit_url,
            "Body Parts": self.body_part,
            "Icon": generate_icon_url(IconType.GYM, IconColor.BROWN)
        }

    def children_blocks(self):
        return generate_children_block_for_crossfit_exercise(self.description, self.tips)

    def get_property_overrides(self) -> Dict:
        """Returns property type overrides for CrossFit exercise creation"""
        return {
            "Name": NotionPropertyType.TITLE,
            "Expertise": NotionPropertyType.SELECT_NAME,
            "Video": NotionPropertyType.URL,
            "Link": NotionPropertyType.URL,
        }


class CrossfitManager:
    def __init__(self, crossfit_exercises_db_id: str):
        self.crossfit_exercises_db_id = crossfit_exercises_db_id
        self.variables_exercises = self.load_crossfit_exercises_from_variables(NEW_EXERCISES)
        self.notion_exercises = []

    def load_crossfit_exercises_from_variables(self, exercises_data: Dict[str, Any]) -> List[CrossfitExercise]:
        """
        Load CrossFit exercises from dictionary data into CrossfitExercise objects
        """
        return [CrossfitExercise(name, data) for name, data in exercises_data.items()]

    def get_crossfit_exercises_in_notion(self):
        crossfit_notion_pages = get_db_pages(self.crossfit_exercises_db_id)
        return self.get_exercises_from_notion(crossfit_notion_pages)

    def get_exercises_from_notion(self, crossfit_notion_pages: list) -> List[CrossfitExercise]:
        """Gets all CrossFit exercises from Notion database"""
        try:
            exercises = []

            for page in crossfit_notion_pages:
                try:
                    exercise = self.create_crossfit_exercise_from_notion(page)
                    exercises.append(exercise)
                except Exception as e:
                    logger.error(f"Error creating exercise from page: {str(e)}")
                    continue

            logger.info(f"Successfully retrieved {len(exercises)} exercises from Notion")
            return exercises

        except Exception as e:
            logger.error(f"Error getting exercises from Notion: {str(e)}")
            return []

    def create_crossfit_exercise_from_notion(self, notion_page: Dict) -> 'CrossfitExercise':
        """Creates CrossfitExercise object from Notion page data"""
        properties = notion_page['properties']

        # Extract properties with error handling
        def get_title(prop_name: str) -> str:
            return properties[prop_name]['title'][0]['plain_text'] if properties[prop_name]['title'] else ""

        def get_multiselect(prop_name: str) -> List[str]:
            return [item['name'] for item in properties[prop_name]['multi_select']] if properties[prop_name][
                'multi_select'] else []

        def get_url(prop_name: str) -> str:
            return properties[prop_name]['url'] if properties[prop_name]['url'] else ""

        def get_expertise(prop_name: str) -> int:
            expertise_level = properties[prop_name]['select']['name'] if properties[prop_name]['select'] else "BEGINNER"
            return expertise_map.get(expertise_level, 1)

        exercise_data = {
            'equipment': get_multiselect('Equipment'),
            'expertise': get_expertise('Expertise'),  # Now returns numeric value
            'demo_url': get_url('Video'),
            'crossfit_url': get_url('Link'),
            'body_part': get_multiselect('Body Parts'),
        }

        return CrossfitExercise(get_title('Name'), exercise_data)

    def add_crossfit_exercises_to_notion(self):
        added_exercises = []
        if not self.notion_exercises:
            self.notion_exercises = self.get_crossfit_exercises_in_notion()

        exercise_names = [exercise.name for exercise in self.notion_exercises]
        for exercise in self.variables_exercises:
            if exercise.name in exercise_names:
                logger.debug(f"{exercise.name} already exists in Notion")
            else:
                try:
                    create_page_with_db_dict_and_children_block(self.crossfit_exercises_db_id, exercise.payload(),
                                                                exercise.children_blocks(), exercise.get_property_overrides())
                except Exception as e:
                    logger.error(f"Error adding {exercise.name} to Notion: {str(e)}")
                    continue
                added_exercises.append(exercise)
                logger.debug(f"Added {exercise.name} to Notion")

        if len(added_exercises) > 0:
            logger.info(f"Successfully dded {len(added_exercises)} new exercises to Notion")


