import re
from typing import Dict, Any, List

from common import capitalize_text_or_list
from crossfit.crossfit_variables import EXERCISES, TRAININGS
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
        self.equipment = self.normalize_equipment_list(data.get('equipment', []))
        self.expertise = data.get('expertise', 1)
        self.expertise_level = self.get_expertise_level()
        self.demo_url = data.get('demo_url', '')
        self.crossfit_url = data.get('crossfit_url', '')
        self.body_part = self.normalize_body_parts(data.get('body_part', []))
        self.description = data.get('description', [])
        self.page_id = ''

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

    def normalize_equipment_list(self, equipment_list):
        """
        Normalize a list of equipment names by:
        - Capitalizing
        - Removing hyphens
        - Converting plurals to singular
        - Standardizing similar terms
        - Making exercise names more understandable
        - Removing plates if barbell is present

        Args:
            equipment_list (list): List of equipment names

        Returns:
            list: List of normalized equipment names
        """

        def normalize_single_name(name):
            # Convert to lowercase for processing
            name = name.lower()

            # Remove hyphens and replace with space
            name = name.replace("-", " ")

            # Dictionary of plural -> singular mappings
            plurals = {
                "dumbbells": "dumbbell",
                "kettlebells": "kettlebell",
                "plates": "plate",
                "parallettes": "parallette",
                "rings": "ring",
                "blocks": "block",
                "boxes": "box"
            }

            # Replace plurals with singular forms
            if name in plurals:
                name = plurals[name]

            # Standardize equipment and exercise names
            equipment_standards = {
                "weight plate": "plate",
                "climbing rope": "rope",
                "jump rope": "rope",
                "pull up bar": "pullup bar",
                "pullup bar": "pullup bar",
                "ghd machine": "ghd",
                "rowing machine": "rower",
                "medicine ball": "med ball",
                "ab mat": "abdominal mat",
                "ab mat sit up": "abdominal mat"
            }

            # Replace with standard names
            for original, standard in equipment_standards.items():
                if name == original:
                    name = standard
                    break

            # Capitalize each word
            name = " ".join(word.capitalize() for word in name.split())

            return name

        # Process list and remove duplicates using set
        normalized_equipment = list(set(normalize_single_name(item) for item in equipment_list))

        # Remove 'Plate' if 'Barbell' is present
        if 'Barbell' in normalized_equipment and 'Plate' in normalized_equipment:
            normalized_equipment.remove('Plate')

        # Sort the list for consistent output
        normalized_equipment.sort()

        return normalized_equipment

    def normalize_body_parts(self, body_parts_list):
        """
        Normalize and simplify a list of body parts into major categories.

        Args:
            body_parts_list (list): List of body part names

        Returns:
            list: List of normalized major body part categories
        """

        def normalize_single_body_part(name):
            # Convert to lowercase for processing
            name = name.lower().strip()

            # Mapping of specific body parts to major categories
            body_part_mapping = {
                # Legs category
                "hip flexors": "legs",
                "hamstrings": "legs",
                "glutes": "legs",
                "hips": "legs",
                "calves": "legs",
                "quads": "legs",

                # Back category
                "upper back": "back",
                "lower back": "back",
                "posterior chain": "back",
                "spine": "back",
                "traps": "back",

                # Core category
                "obliques": "abs",
                "core": "abs",
                "abdomininals": "abs",

                # Shoulders category
                "deltoids": "shoulders",
                "rotator cuff": "shoulders",
                "rotation": "shoulders",

                # Keep these as is
                "chest": "chest",
                "biceps": "arms",
                "triceps": "arms",
                "forearms": "arms",
                "cardio": "cardio",

                # Functional categories to be mapped to major muscle groups
                "power": "full body",
                "stability": "core",
                "coordination": "full body",
                "balance": "full body",
                "agility": "full body",
                "mobility": "full body",
                "groin": "legs",
                "full body": "full body"
            }

            return body_part_mapping.get(name, name)

        # Process list and remove duplicates
        normalized_parts = list(set(normalize_single_body_part(part) for part in body_parts_list))

        # Define the order of major categories
        category_order = [
            "full body",
            "legs",
            "back",
            "chest",
            "arms",
            "shoulders",
            "core",
            "cardio"
        ]

        # Filter out any categories not in our main list and sort by predefined order
        final_parts = [part.capitalize() for part in category_order if part in normalized_parts]

        return final_parts


class CrossfitWorkout:
    def __init__(self, exercise_used: list, training_program: dict, training_type: str, duration: int):
        self.exercise_used = exercise_used
        self.training_type = training_type
        self.duration = duration
        self.workout_program = training_program
        self.name = ''
        self.page_id = ''

    def __str__(self) -> str:
        return f"{self.training_type} - {self.duration} minutes"

    def __repr__(self) -> str:
        return f"CrossfitTraining(exercise_used={self.exercise_used}, training_type={self.training_type}, " \
               f"duration={self.duration}, training_program={self.workout_program})"

    def payload(self) -> Dict:
        """Creates a Notion database payload for a CrossFit training"""
        return {
            "Training Type": self.training_type,
            "Duration": self.duration,
            "Exercise Used": self.exercise_used,
            "Training Program": self.workout_program,
            "Icon": generate_icon_url(IconType.GYM, IconColor.BROWN)
        }


class CrossfitManager:
    def __init__(self, crossfit_exercises_db_id: str, crossfit_workout_db_id: str):
        self.crossfit_exercises_db_id = crossfit_exercises_db_id
        self.variables_exercises = self.load_crossfit_exercises_from_variables(EXERCISES)
        self.notion_exercises = []

        # self.crossfit_workouts_db_id = crossfit_workout_db_id
        # self.variables_workouts = self.load_crossfit_workouts_from_variables(TRAININGS)
        # self.notion_workouts = []

    def get_exercise_by_name(self, exercise_name):
        return self.match_exercise(exercise_name, self.notion_exercises)

    def normalize_exercise_name(self, name):
        def normalize_text(text):
            # Convert to lowercase and remove special characters but preserve spaces
            text = text.lower().strip()
            # Replace hyphens and special characters with spaces
            text = text.replace('-', ' ').replace('&', ' ').replace('/', ' ').replace('+', ' ')
            # Remove periods and other punctuation
            text = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in text)
            # Normalize multiple spaces
            return ' '.join(text.split())

        def get_abbreviation(text):
            """Return the standard abbreviation for common CrossFit movements"""
            abbreviations = {
                'handstand push up': 'HSPU',
                'toes to bar': 'T2B',
                'chest to bar': 'C2B',
                'knees to elbow': 'K2E',
                'glute ham developer': 'GHD',
                'clean and jerk': 'C&J',
                'overhead squat': 'OHS'
            }
            return abbreviations.get(text.lower(), '')

        def expand_abbreviations(text):
            """Expand common CrossFit abbreviations"""
            abbreviations = {
                'hspu': 'handstand push up',
                't2b': 'toes to bar',
                'du': 'double under',
                'c2b': 'chest to bar',
                'k2e': 'knees to elbow',
                'ghd': 'glute ham developer',
                'kb': 'kettlebell',
                'db': 'dumbbell',
                'bb': 'barbell',
                'rdl': 'romanian deadlift',
                'cal': 'calorie',
                'med': 'medicine',
                'ohs': 'overhead squat',
                'alt': 'alternative'
            }

            words = text.split()
            for i, word in enumerate(words):
                if word.lower() in abbreviations:
                    words[i] = abbreviations[word.lower()]
            return ' '.join(words)

        def standardize_compound_words(text):
            """Standardize compound exercise names"""
            compound_patterns = {
                r'\b(step|push|pull|press|jump|get)(?:\s+)?(?:up|ups)\b': r'\1 up',
                r'\b(hand)\s+?stand\b': r'handstand',
                r'\brunning\b': 'run',
                # Special case for 'clean jerk' - always add 'and'
                r'\bclean\s+(?:&\s+)?jerk\b': 'clean and jerk',
                r'\bclean\s+jerk\b': 'clean and jerk'
            }

            for pattern, replacement in compound_patterns.items():
                text = re.sub(pattern, replacement, text)
            return text

        def expand_equipment_abbreviations(text):
            """Handle equipment abbreviations"""
            equipment_abbrev = {
                r'\bdb\b': 'dumbbell',
                r'\bkb\b': 'kettlebell',
                r'\bbb\b': 'barbell',
            }

            for abbrev, full in equipment_abbrev.items():
                text = re.sub(abbrev, full, text, flags=re.IGNORECASE)
            return text

        def standardize_exercise_plurals(text):
            """Handle special cases for exercise name plurals"""
            # Words that should always be singular
            always_singular = {
                'pull up', 'push up', 'step up', 'clean', 'snatch', 'jerk',
                'press', 'swing', 'squat', 'deadlift', 'row', 'run', 'muscle up'
            }

            # Compound exercises that should be preserved entirely
            preserve_compounds = {
                'plate hold', 'front rack', 'wall walk', 'wall ball'
            }

            # First check if text is a preserved compound
            text_lower = text.lower()
            if text_lower in preserve_compounds:
                return text_lower

            # Normalize compound exercises
            normalized = text_lower
            normalized = re.sub(r'box jump(?:\s+over)?', 'box jump', normalized)  # Remove "over" from box jump

            words = normalized.split()
            normalized_words = []

            for word in words:
                # Check if word is part of a compound exercise name
                base_word = word.rstrip('s')
                if base_word.lower() in always_singular:
                    normalized_words.append(base_word)
                else:
                    normalized_words.append(word)

            return ' '.join(normalized_words)

        # Remove common suffixes and prefixes that don't change the exercise
        removable_terms = [
            'warm up', 'warmup', 'drill', 'drills', 'progression', 'work',
            'hold', 'holds', 'variations', 'shots'
        ]

        # First normalize basic text
        normalized = normalize_text(name)

        # Store if name starts with 'strict' and remove it temporarily
        is_strict = normalized.lower().startswith('strict')
        if is_strict:
            normalized = normalized[len('strict'):].strip()

        # Expand equipment abbreviations first
        normalized = expand_equipment_abbreviations(normalized)

        # Expand other abbreviations
        normalized = expand_abbreviations(normalized)

        # Remove removable terms
        for term in removable_terms:
            normalized = normalized.replace(term, '').strip()

        # Standardize compound words (including Clean And Jerk)
        normalized = standardize_compound_words(normalized)

        # Handle plurals
        normalized = standardize_exercise_plurals(normalized)

        # Handle equipment combinations (like "Dumbbell Kettlebell")
        if 'dumbbell kettlebell' in normalized.lower() or 'kettlebell dumbbell' in normalized.lower():
            normalized = re.sub(r'\b(dumbbell|kettlebell)\s+(dumbbell|kettlebell)\b',
                                'dumbbell', normalized, flags=re.IGNORECASE)

        # Add back 'Strict' prefix if it was present
        if is_strict:
            normalized = 'Strict ' + normalized

        # Capitalize each word
        normalized = ' '.join(word.capitalize() for word in normalized.split())

        # Add abbreviation if available
        abbrev = get_abbreviation(normalized)
        if abbrev:
            normalized = f"{normalized} ({abbrev})"

        return normalized

    def match_exercise(self, normalized_name, exercise_list):
        """
        Checks if a normalized exercise name exists in the exercise list.
        Returns the matching exercise if found, None otherwise.
        """
        normalized_name = normalized_name.lower()
        for exercise in exercise_list:
            if self.normalize_exercise_name(exercise.name).lower() == normalized_name:
                return exercise
        return None

    def load_crossfit_exercises_from_variables(self, exercises_data: Dict[str, Any]) -> List[CrossfitExercise]:
        """
        Load CrossFit exercises from dictionary data into CrossfitExercise objects
        """
        return [CrossfitExercise(self.normalize_exercise_name(name), data) for name, data in exercises_data.items()]

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

    def create_crossfit_exercise_from_notion(self, notion_page: Dict) -> CrossfitExercise:
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
            'id': notion_page['id']
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
                                                                exercise.children_blocks(),
                                                                exercise.get_property_overrides())
                except Exception as e:
                    logger.error(f"Error adding {exercise.name} to Notion: {str(e)}")
                    continue
                added_exercises.append(exercise)
                logger.debug(f"Added {exercise.name} to Notion")

        if len(added_exercises) > 0:
            logger.info(f"Successfully added {len(added_exercises)} new exercises to Notion")

    def load_crossfit_workouts_from_variables(self, workout_data: Dict[str, Any],
                                              break_if_miss_exercise=False) -> List[CrossfitWorkout]:
        """
        Load CrossFit exercises from dictionary data into CrossfitExercise objects
        """
        if not self.notion_exercises:
            self.notion_exercises = self.get_crossfit_exercises_in_notion()

        workout_list = []
        missing_exercise_names = []
        for workout in workout_data:
            workout_keys = list(workout.keys())
            if len(workout_keys) == 1:
                workout = workout[workout_keys[0]]
            elif len(workout_keys) == 2:
                workout = workout['metcon']
            try:
                exercise_list = []
                for workout_exercise in workout['exercises_used']:
                    exercise = self.get_exercise_by_name(workout_exercise)
                    if not exercise:
                        missing_exercise_names.append(workout_exercise)
                    else:
                        exercise_list.append(exercise)
                exercises_used = exercise_list
                training_program = workout['training_program']
                training_type = workout['training_type']
                duration = workout['training_time']
                workout_list.append(CrossfitWorkout(exercises_used, training_program, training_type, duration))
            except Exception as e:
                logger.error(f"There is an issue while loading: {str(e)}")
        if missing_exercise_names:
            sorted_missing_names = sorted(list(set(missing_exercise_names)))
            error_message = f"These required exercises don't exist in Notion: {set(sorted_missing_names)}"
            logger.error(error_message)
            if break_if_miss_exercise:
                raise Exception(error_message)
        return workout_list

    def get_crossfit_workouts_in_notion(self):
        crossfit_notion_pages = get_db_pages(self.crossfit_workouts_db_id)
        # return self.get_workouts_from_notion(crossfit_notion_pages)
        return []

    def get_workouts_from_notion(self, crossfit_notion_pages: list) -> List[CrossfitExercise]:
        """Gets all CrossFit exercises from Notion database"""
        try:
            trainings = []

            for page in crossfit_notion_pages:
                try:
                    training = self.create_crossfit_workout_from_notion(page)
                    trainings.append(training)
                except Exception as e:
                    logger.error(f"Error creating training from page: {str(e)}")
                    continue

            logger.info(f"Successfully retrieved {len(trainings)} trainings from Notion")
            return trainings

        except Exception as e:
            logger.error(f"Error getting trainings from Notion: {str(e)}")
            return []

    def create_crossfit_workout_from_notion(self, notion_page: Dict) -> CrossfitExercise:
        """Creates CrossfitExercise object from Notion page data"""
        properties = notion_page['properties']

        # Extract properties with error handling
        def get_title(prop_name: str) -> str:
            return properties[prop_name]['title'][0]['plain_text'] if properties[prop_name]['title'] else ""

        def get_multiselect(prop_name: str) -> List[str]:
            return [item['name'] for item in properties[prop_name]['multi_select']] if properties[prop_name][
                'multi_select'] else []

        def get_select(prop_name: str) -> List[str]:
            return [item['name'] for item in properties[prop_name]['select']] if properties[prop_name][
                'select'] else []

        def get_url(prop_name: str) -> str:
            return properties[prop_name]['url'] if properties[prop_name]['url'] else ""

        def get_expertise(prop_name: str) -> int:
            expertise_level = properties[prop_name]['select']['name'] if properties[prop_name]['select'] else "BEGINNER"
            return expertise_map.get(expertise_level, 1)

        exercise_data = {
            'name': get_title('Name'),
            'type': get_select('Type'),
            'expertise': get_expertise('Expertise'),  # Now returns numeric value
            'demo_url': get_url('Video'),
            'crossfit_url': get_url('Link'),
            'body_part': get_multiselect('Body Parts'),
        }

        return CrossfitWorkout(get_title('Name'), exercise_data)

    def add_crossfit_workouts_to_notion(self):
        added_workouts = []
        if not self.notion_workouts:
            self.notion_workouts = self.get_crossfit_workouts_in_notion()

        exercise_names = [exercise.name for exercise in self.notion_exercises]
        for exercise in self.variables_exercises:
            if exercise.name in exercise_names:
                logger.debug(f"{exercise.name} already exists in Notion")
            else:
                try:
                    create_page_with_db_dict_and_children_block(self.crossfit_exercises_db_id, exercise.payload(),
                                                                exercise.children_blocks(),
                                                                exercise.get_property_overrides())
                except Exception as e:
                    logger.error(f"Error adding {exercise.name} to Notion: {str(e)}")
                    continue
                added_workouts.append(exercise)
                logger.debug(f"Added {exercise.name} to Notion")

        if len(added_workouts) > 0:
            logger.info(f"Successfully dded {len(added_workouts)} new exercises to Notion")
