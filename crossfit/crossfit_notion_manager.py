import re
from typing import Dict, Any, List, Optional

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


class CrossfitTmpExercise(CrossfitExercise):
    def __init__(self, name: str):
        data = {
            'tips': [],
            'equipment': [],
            'expertise': 1,
            'demo_url': '',
            'crossfit_url': '',
            'body_part': [],
            'description': []
        }
        super().__init__(name, data)


class CrossfitWorkout:
    def __init__(self, exercise_used: list, training_program: dict, training_type: str, duration: Optional[int],
                 original_training_program=None):
        self.exercise_used = exercise_used
        self.training_type = training_type
        self.duration = duration
        self.program = training_program
        self.original_program = original_training_program
        self.name = ''
        self.page_id = ''

    def get_icon(self):
        color = IconColor.LIGHT_GRAY
        if self.training_type.lower() == "metcon":
            color = IconColor.PURPLE
        elif self.training_type.lower() == "strength":
            color = IconColor.GRAY
        elif self.training_type.lower() == "warm-up":
            color = IconColor.ORANGE
        return generate_icon_url(IconType.RUN, color)

    def get_exercises_str(self):
        exercises_str = ''
        for exercise in self.exercise_used:
            exercises_str += f"{exercise.name}, "
        exercises_str = exercises_str[:-2]

        return exercises_str

    def get_workout_program_str(self):
        workout_str = ''
        for workout_program_keys in self.program.keys():
            workout_str += f"{workout_program_keys}\n"
            for workout_program_key in self.program[workout_program_keys].keys():
                workout_str += f"{workout_program_key}: {self.program[workout_program_keys][workout_program_key]}\n"
            workout_str += "\n"
        return workout_str

    def __str__(self) -> str:
        try:
            workout_str = f"Workout: {self.get_title()}\n"
            workout_str += f"Training type: {self.training_type}\n"
            workout_str += f"Header: {self.get_workout_header()}\n\n"
            workout_str += f"Exercises: {self.get_exercises_str()}\n"
            workout_str += f"Program: {self.get_workout_program_str()}\n"

        except Exception as e:
            logger.error(f"Error converting workout to string: {str(e)}")
            workout_str = f"Error converting workout to string: {str(e)}"

        return workout_str

    def __repr__(self) -> str:
        return f"CrossfitTraining(exercise_used={self.exercise_used}, training_type={self.training_type}, " \
               f"duration={self.duration}, training_program={self.program})"

    def get_workout_header(self, print=False):
        workout_types = list(self.program.keys())
        for workout_type in workout_types:
            normalized_workout = self.normalize_training_format(workout_type).capitalize()
            if print:
                logger.debug(f"Original: {workout_type} - Normalized: {normalized_workout}")
            return normalized_workout

    def get_title(self, print=False):
        if not self.name:
            self.name = self.get_shorter_format() + f" - {self.duration} min - " + self.get_exercise_names_str()
        if print:
            logger.debug(self.name)
        return self.name

    def get_shorter_format(self):
        workout_types_str = ', '.join(self.program.keys())
        return workout_types_str

    def get_exercise_names(self):
        return [exercise.name for exercise in self.exercise_used]

    def get_exercise_names_str(self):
        return ', '.join(self.get_exercise_names())

    def normalize_training_format(self, format_str: str) -> str:
        try:
            # Common abbreviations
            abbreviations = {
                "AMRAP": "As Many Repetitions As Possible",
                "EMOM": "Every Minute On the Minute",
                "RFT": "Rounds For Time"
            }

            format_str = format_str.strip()

            # Handle AMRAP formats
            if format_str.startswith("AMRAP"):
                time = format_str.split()[1]
                return f"{abbreviations['AMRAP']} (AMRAP) for {time} min"

            # Handle EMOM formats
            if format_str.startswith("EMOM"):
                time_split = format_str.split()
                if len(time_split) > 1:
                    time = time_split[1]
                else:
                    time = self.duration
                return f"{abbreviations['EMOM']} (EMOM) for {time} min"

            # Handle "Every X min x Y" formats
            if format_str.startswith("Every"):
                return format_str.replace("x", "for") + " sets"

            # Handle "For Time" formats
            if format_str.startswith("For"):
                time = self.duration if self.duration else ""
                time_str = f" - {time} min" if time else ""
                return f"For Time{time_str}"

            # Handle numbered rounds (e.g. "3 Rounds")
            if any(c.isdigit() for c in format_str) and "Round" in format_str:
                return f"{format_str} For Time"

            # Handle descending rep schemes
            if "-" in format_str and all(x.isdigit() for x in format_str.split("-")):
                return f"Descending Reps Scheme: {format_str}"

            # Handle Death by formats
            if format_str.startswith("Death"):
                return "Death By (Ascending Reps Until Failure)"

            return format_str
        except Exception as e:
            logger.error(f"Error normalizing training format: {str(e)}")
            return format_str

    def payload(self) -> Dict:
        """Creates a Notion database payload for a CrossFit training"""
        return {
            "Training Type": self.training_type,
            "Duration": self.duration,
            "Exercise Used": self.exercise_used,
            "Training Program": self.program,
            "Icon": generate_icon_url(IconType.GYM, IconColor.BROWN)
        }


class CrossfitManager:
    def __init__(self, crossfit_exercises_db_id: str, crossfit_workout_db_id: str):
        self.crossfit_exercises_db_id = crossfit_exercises_db_id
        self.variables_exercises = self.load_crossfit_exercises_from_variables(EXERCISES)
        self.notion_exercises = self.get_crossfit_exercises_in_notion()

        self.crossfit_workouts_db_id = crossfit_workout_db_id
        # ariel = self.get_exercise_by_name('Running')
        self.variables_workouts = self.load_crossfit_workouts_from_variables(TRAININGS)
        self.notion_workouts = []
        self.print_workouts()

    def print_workouts(self):
        for i, workout in enumerate(self.variables_workouts):
            logger.debug(f"{i + 1}\n{str(workout)}")

    def get_notion_exercise_names(self):
        return sorted([exercise.name for exercise in self.notion_exercises])

    def get_exercise_by_name(self, exercise_name):
        """
        Returns (found: bool, exercise_name: str)
        found: True if matching exercise exists, False if no match
        exercise_name: Mapped exercise name if found, original name if not found
        """
        normalized_name = self.map_exercise_name(exercise_name, self.get_notion_exercise_names())
        found = normalized_name in self.get_notion_exercise_names()
        return found, normalized_name

    def map_exercise_name(self, name: str, known_exercises: list) -> str:
        # Skip words check
        skip_words = ['partner', 'warm up', 'warmup', 'drill', 'progression', 'practice', 'game']
        if any(word in name.lower() for word in skip_words):
            return ''

        # Manual mappings - canonical form as key, variations as values
        manual_mappings = {
            "inchworm": ["inch worm", "inch worms"],
            "weighted abmat sit up": ["weighted abmat sit ups"],
            "alternating lunge": ["alternating lunges"],
            "medicine ball pass": ["med ball pass", "med ball passes"],
            "toes to bar": ["toe to bar", "toes to bars"],
            "handstand push up": ["handstand pushup", "handstand push ups"],
            "muscle up": ["muscle ups"],
            "pull up": ["pull ups"],
            "push up": ["push ups"],
            "row": ["rows", "assault bike", "cal assault", "row bike", "machine row", "cal machine", "machine"],
            "squat": ["squats"],
            "lunge": ["lunges"],
            "jump": ["jumps"],
            "clean and jerk": ["clean jerk", "clean & jerk"],
            "devils press": ["devil press"],
            "run": ["running"],
        }

        # Abbreviation mappings - canonical form as key, abbreviations as values
        abbrev_map = {
            'dumbbell': ['db'],
            'kettlebell': ['kb'],
            'pvc': ['pvc'],
            'toes to bar': ['t2b'],
            'handstand push up': ['hspu'],
            'chest to bar': ['c2b'],
            'kettlebell swing': ['kbs'],
            'knees to elbow': ['k2e'],
            'glute ham developer': ['ghd'],
            'ab mat': ['abmat'],
            'medicine ball': ['med ball'],
            'overhead squat': ['ohs'],
            'clean and jerk': ['c&j'],
            'ground to overhead': ['gto'],
            'romanian deadlift': ['rdl'],
            'alternative': ['alt'],
        }

        def normalize_text(text):
            text = text.lower().strip()
            text = text.replace('-', ' ')
            # Find canonical form if it exists in manual mappings
            for canonical, variations in manual_mappings.items():
                if text in variations or text == canonical.lower():
                    return canonical
            return text

        def expand_abbreviations(text):
            words = text.split()
            expanded_words = []
            for word in words:
                word_lower = word.lower()
                expanded = word
                # Check if word matches any abbreviation
                for canonical, abbrevs in abbrev_map.items():
                    if word_lower in abbrevs:
                        expanded = canonical
                        break
                expanded_words.append(expanded)
            return ' '.join(expanded_words)

        def standardize_exercises(text):
            # Standardize compound movements
            compound_patterns = {
                'box jump over': 'box jump',
                'burpee box jump over': 'burpee box jump',
                'bar facing burpee': 'bar facing burpee',
                'chest to bar pull up': 'chest to bar pull up',
                'toes to bar': 'toes to bar',
                'knees to elbow': 'knees to elbows'
            }

            for pattern, replacement in compound_patterns.items():
                if pattern in text:
                    return replacement
            return text

        # Process name
        norm_name = normalize_text(name)
        norm_name = expand_abbreviations(norm_name)
        norm_name = standardize_exercises(norm_name)

        # Create normalized dictionary of known exercises
        norm_exercises = {normalize_text(standardize_exercises(expand_abbreviations(ex))): ex
                          for ex in known_exercises}

        # Try exact matches
        if norm_name in norm_exercises:
            return norm_exercises[norm_name]

        # Try partial matches
        for norm_known, original in norm_exercises.items():
            if norm_name in norm_known or norm_known in norm_name:
                return original

        # Return processed version if no match found
        return norm_name.title()

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

        def standardize_compound_movements(text):
            """Standardize compound movement names"""
            compound_patterns = {
                r'box jump[- ]?over': 'box jump',
                r'devils?\s*press': 'devil press',
                r'burpee[- ]?box[- ]?jump[- ]?over': 'burpee box jump over',
                r'bar[- ]?facing[- ]?burpee': 'bar facing burpee',
                r'chest[- ]?to[- ]?bar': 'chest to bar',
                r'toes[- ]?to[- ]?bar': 'toes to bar',
                r'knees[- ]?to[- ]?elbow': 'knees to elbow',
                r'rowing|machine\s+row(?:\s+bike)?|row\s+bike': 'row'
            }

            text = text.lower()
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
            text = re.sub(r"'s$|s'$", "", text)

            always_singular = {
                'devil press', 'pull up', 'push up', 'step up', 'clean',
                'snatch', 'jerk', 'press', 'swing', 'squat', 'deadlift',
                'row', 'run', 'muscle up'
            }

            # Map both singular and plural forms
            always_plural = {
                'double under': 'double unders',
                'double unders': 'double unders',
                'toes to bar': 'toes to bar',
                'knees to elbow': 'knees to elbow'
            }

            words = text.lower().split()
            joined_words = ' '.join(words)

            if joined_words in always_plural:
                return always_plural[joined_words]

            normalized_words = []
            for word in words:
                base_word = word.rstrip('s')
                if base_word in always_singular:
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

        normalized = standardize_exercise_plurals(normalized)
        normalized = standardize_compound_movements(normalized)

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

    def load_crossfit_workouts_from_variables(self, workout_data: Dict[str, Any], break_if_miss_exercise=False) -> List[
        CrossfitWorkout]:
        workout_list = []
        missing_exercise_names = []

        for workout in workout_data:
            workout_keys = list(workout.keys())
            original_workout = workout.copy()  # Store original workout data
            original_workout = original_workout['training_program']  # Store original workout data

            if len(workout_keys) == 1:
                workout = workout[workout_keys[0]]
            elif len(workout_keys) == 2:
                workout = workout['metcon']

            try:
                exercise_list = []
                # Map exercises to their Notion counterparts
                exercise_mapping = {}  # To store original name -> Notion exercise mapping

                for workout_exercise in workout['exercises_used']:
                    found, exercise_name = self.get_exercise_by_name(workout_exercise)
                    if not found and exercise_name != '':
                        missing_exercise_names.append(exercise_name)
                    else:
                        matching_exercise = next((ex for ex in self.notion_exercises if ex.name == exercise_name), None)
                        if matching_exercise:
                            exercise_list.append(matching_exercise)
                            exercise_mapping[workout_exercise] = matching_exercise

                # Create a deep copy of the training program to modify
                modified_program = self.replace_exercises_in_program(
                    workout['training_program'],
                    exercise_mapping
                )

                exercises_used = exercise_list
                training_type = workout['training_type']
                duration = workout['training_time']
                converted_duration = (
                    duration if isinstance(duration, int)
                    else None if duration == "until failure" or duration is None
                    else int(duration) if str(duration).isdigit()
                    else None
                )

                workout_obj = CrossfitWorkout(
                        exercises_used,
                        modified_program,
                        training_type,
                        converted_duration,
                        original_workout
                    )

                workout_list.append(workout_obj)

            except Exception as e:
                logger.error(f"There is an issue while loading: {str(e)}")

        if missing_exercise_names:
            sorted_missing_names = sorted(list(set(missing_exercise_names)))
            error_message = f"These required exercises don't exist in Notion: {sorted_missing_names}"
            logger.error(error_message)
            if break_if_miss_exercise:
                raise Exception(error_message)

        logger.info(f"Loaded {len(workout_list)} workouts from variables")
        return workout_list

    def replace_exercises_in_program(self, program: Dict, exercise_mapping: Dict) -> Dict:
        if isinstance(program, dict):
            new_program = {}
            for key, value in program.items():
                # Check if this is a leaf node (exercise details dictionary)
                if isinstance(value, dict) and not any(isinstance(v, dict) for v in value.values()):
                    # This is an exercise entry, try to map it
                    found, exercise_name = self.get_exercise_by_name(key)
                    if found:
                        matching_exercise = next((ex for ex in exercise_mapping.values()
                                                  if ex.name == exercise_name), None)
                        new_key = matching_exercise if matching_exercise else CrossfitTmpExercise(exercise_name)
                    else:
                        new_key = key
                    new_program[new_key] = value
                else:
                    # This is an intermediate node, keep traversing
                    new_program[key] = self.replace_exercises_in_program(value, exercise_mapping)
            return new_program
        elif isinstance(program, list):
            return [self.replace_exercises_in_program(item, exercise_mapping) for item in program]
        else:
            return program

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
