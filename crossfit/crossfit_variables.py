import re

EXERCISES = {
    "Jumping Squat": {
        "tips": [
            "Land softly with knees tracking over toes",
            "Use arms to help generate power",
            "Maintain tight core throughout movement",
            "Control descent into next rep"
        ],
        "equipment": [],  # Bodyweight version - can be loaded with DBs/KB for advanced
        "expertise": 2,  # More technical than air squat but still accessible
        "demo_url": "https://www.youtube.com/watch?v=CTxYfJ1qN8Y",
        "crossfit_url": "",
        "body_part": ["legs"],
        "description": [
            "Start with feet shoulder width apart",
            "Lower into quarter to half squat position",
            "Keep chest up and core engaged",
            "Drive arms up as you explode through legs",
            "Extend hips, knees, and ankles powerfully",
            "Jump straight up reaching full extension",
            "Land softly with bent knees to absorb impact",
            "Immediately transition into next rep",
            "Maintain rhythm and control throughout"
        ]
    },
    "Push Up": {
        "tips": [
            "Keep core tight and body in straight line",
            "Hands slightly wider than shoulder width",
            "Lower chest to ground controlling descent",
            "Push through full palm maintaining body tension"
        ],
        "equipment": [],  # Bodyweight movement
        "expertise": 1,  # Fundamental movement
        "demo_url": "https://www.youtube.com/watch?v=0pkjOk0EiAk",
        "crossfit_url": "https://www.crossfit.com/essentials/push-up",
        "body_part": ["chest", "shoulders", "triceps", "core"],
        "description": [
            "Start in high plank position with hands shoulder-width apart",
            "Keep body in straight line from head to heels",
            "Lower body as one unit until chest touches ground",
            "Keep elbows at roughly 45 degree angle from body",
            "Push back to starting position maintaining body alignment",
            "Breathe steadily throughout movement",
            "Maintain full body tension",
            "Reset position before next rep"
        ]
    },
    "Snatch": {
        "tips": [
            "Keep bar close throughout pull",
            "Complete full extension before pulling under",
            "Aggressive turnover to secure overhead position"
        ],
        "equipment": ["barbell", "plates"],
        "expertise": 5,
        "demo_url": "https://www.youtube.com/watch?v=9xQp2sldyts",
        "crossfit_url": "https://www.crossfit.com/essentials/the-snatch",
        "body_part": ["full body", "shoulders", "legs", "back"],
        "description": [
            "Start with feet hip-width, bar over midfoot",
            "Wide grip outside knees, hook grip recommended",
            "Shoulders over or slightly ahead of bar",
            "First pull: maintain back angle while bar breaks ground",
            "Second pull: explosively extend hips as bar passes thighs",
            "Third pull: pull body under bar while keeping arms straight",
            "Turn elbows out and punch up to receive bar overhead",
            "Catch in overhead squat position with active shoulders",
            "Stand to full extension with bar stabilized overhead"
        ]
    },
    "Clean and Jerk": {
        "tips": [
            "Keep bar close during clean pull",
            "Stand fully before starting jerk",
            "Time split under bar in jerk"
        ],
        "equipment": ["barbell", "plates"],
        "expertise": 5,
        "demo_url": "https://www.youtube.com/watch?v=yDmrJBPWhYA",
        "crossfit_url": "https://www.crossfit.com/essentials/clean-and-jerk",
        "body_part": ["full body", "legs", "shoulders"],
        "description": [
            "Start with bar over midfoot in clean position",
            "Perform clean pull keeping bar close",
            "Receive in front rack position",
            "Stand completely before jerk",
            "Perform quick dip and drive",
            "Split legs while pressing bar overhead",
            "Land with bar locked out overhead",
            "Front foot flat, back heel up",
            "Return feet to center, maintaining overhead position"
        ]
    },
    "Muscle Up": {
        "tips": [
            "Generate power from hollow-to-arch swing",
            "Keep false grip throughout movement",
            "Stay close to rings/bar during transition"
        ],
        "equipment": ["rings", "pull-up bar"],
        "expertise": 5,
        "demo_url": "https://www.youtube.com/watch?v=astSQRh1-i0",
        "crossfit_url": "",
        "body_part": ["shoulders", "chest", "back", "core"],
        "description": [
            "Start in a dead hang position with false grip",
            "Initiate with powerful kip swing from hollow to arch",
            "As you reach peak of swing, explosively pull to sternum",
            "Keep elbows close during transition phase",
            "As chest reaches height, quickly rotate wrists and drive elbows back",
            "Push away to achieve support position",
            "Extend arms fully at top position",
            "Lower under control to starting position"
        ]
    },
    "Handstand Push-up": {
        "tips": [
            "Stack shoulders directly over hands",
            "Keep core tight and maintain hollow body",
            "Use slight head movement forward on descent"
        ],
        "equipment": ["wall"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=0wDEO6shVjc",
        "crossfit_url": "",
        "body_part": ["shoulders", "triceps", "core"],
        "description": [
            "Start in handstand position against wall",
            "Keep fingers spread and knuckles gripping floor",
            "Maintain hollow body position with ribs tucked",
            "Lower head between hands in controlled descent",
            "Touch head to ground or AbMat",
            "Press back to full handstand position",
            "Keep elbows tracking forward throughout",
            "Maintain full body tension throughout"
        ]
    },
    "Thruster": {
        "tips": [
            "Maintain front rack position",
            "Drive explosively from bottom of squat",
            "Time press with hip drive"
        ],
        "equipment": ["barbell", "plates"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=L219ltL15zk",
        "crossfit_url": "https://www.crossfit.com/essentials/thruster",
        "body_part": ["legs", "shoulders", "core"],
        "description": [
            "Start with barbell in front rack position",
            "Feet shoulder width apart",
            "Maintain high elbows throughout movement",
            "Descend into full front squat",
            "Drive explosively from bottom position",
            "Use momentum from hip drive to help press",
            "Push head through arms at top",
            "Finish with bar overhead, arms locked",
            "Return bar to front rack position for next rep"
        ]
    },
    "Double Unders": {
        "tips": [
            "Focus on wrist rotation rather than big arm movements",
            "Jump with pointed toes and maintain consistent bounce height",
            "Keep elbows close to ribs for better rope control"
        ],
        "equipment": ["jump rope"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=82jNjDS19lg",
        "crossfit_url": "https://www.crossfit.com/essentials/double-under",
        "body_part": ["calves", "shoulders", "forearms"],
        "description": [
            "Stand tall with rope behind body",
            "Keep elbows close to sides throughout movement",
            "Jump with pointed toes and consistent height",
            "Use wrists to rotate rope twice under feet per jump",
            "Land softly on balls of feet",
            "Maintain straight but relaxed arms",
            "Time rope rotation with jump apex",
            "Keep jumps small and efficient"
        ]
    },
    "Toes to Bar": {
        "tips": [
            "Begin with hollow body position",
            "Generate power from shoulders and lats",
            "Keep core tight throughout movement"
        ],
        "equipment": ["pull-up bar"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=_03pCKOv4l4",
        "crossfit_url": "https://www.crossfit.com/essentials/toes-to-bar",
        "body_part": ["core", "grip", "shoulders"],
        "description": [
            "Hang from pull-up bar with hands just outside shoulders",
            "Start in hollow body position",
            "Generate swing from shoulders",
            "Keep arms straight throughout movement",
            "Drive toes up to touch bar",
            "Control descent back to hollow",
            "Maintain rhythm between reps",
            "Keep core engaged throughout"
        ]
    },
    "Kipping Pull-up": {
        "tips": [
            "Generate power from hollow-to-arch swing",
            "Time pull with forward swing",
            "Keep core tight throughout movement"
        ],
        "equipment": ["pull-up bar"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=lzRo-4pqxPg",
        "crossfit_url": "https://www.crossfit.com/essentials/kipping-pull-up",
        "body_part": ["back", "shoulders", "core"],
        "description": [
            "Start in hollow position with arms fully extended",
            "Swing to arch position pushing chest away from bar",
            "Return to hollow position generating momentum",
            "Time pull with forward swing",
            "Drive elbows down and back",
            "Pull chin over bar",
            "Push away from bar at top",
            "Return to hollow position for next rep"
        ]
    },
    "Chest to Bar Pull-up": {
        "tips": [
            "Use aggressive kip swing",
            "Pull elbows back and down",
            "Touch chest at same spot each rep"
        ],
        "equipment": ["pull-up bar"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=p9Stan68FYM",
        "crossfit_url": "https://www.crossfit.com/essentials/chest-to-bar",
        "body_part": ["back", "shoulders", "chest"],
        "description": [
            "Start in hang position with full arm extension",
            "Generate power with kipping swing",
            "Pull aggressively as hips come forward",
            "Drive elbows down and back",
            "Pull until chest touches bar",
            "Maintain consistent contact point",
            "Push away from bar on descent",
            "Return to hollow position for next rep"
        ]
    },
    "Ring Muscle Up": {
        "tips": [
            "Maintain false grip throughout movement",
            "Pull rings to nipple line before transition",
            "Turn rings out aggressively in support position"
        ],
        "equipment": ["rings"],
        "expertise": 5,
        "demo_url": "https://www.youtube.com/watch?v=47NYqJZz494",
        "crossfit_url": "",
        "body_part": ["shoulders", "chest", "back", "core"],
        "description": [
            "Begin with false grip on rings",
            "Start in hollow position",
            "Generate power through kipping swing",
            "Pull rings to nipple height",
            "Keep elbows close during transition",
            "Turn rings out during support phase",
            "Press to full lockout",
            "Control descent back to hang"
        ]
    },
    "Bar Muscle Up": {
        "tips": [
            "Begin with false grip and hollow body position",
            "Pull explosively to hip height before transition",
            "Keep bar close during turnover to support position"
        ],
        "equipment": ["pull-up bar"],
        "expertise": 5,
        "demo_url": "https://www.youtube.com/watch?v=OCg3UXgzftc",
        "crossfit_url": "",
        "body_part": ["shoulders", "back", "chest", "core"],
        "description": [
            "Start with false grip on pull-up bar",
            "Begin in hollow body position",
            "Generate power with kipping swing",
            "Pull explosively, bringing hips to bar",
            "Keep bar close during turnover",
            "Drive hands down to achieve support",
            "Extend arms fully at top",
            "Lower under control to starting position"
        ]
    },
    "Power Clean": {
        "tips": [
            "Start with bar close to shins",
            "Time hip contact with full extension",
            "Meet bar aggressively with elbows through"
        ],
        "equipment": ["barbell", "plates"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=KjGvwQl8tis",
        "crossfit_url": "https://www.crossfit.com/essentials/power-clean",
        "body_part": ["legs", "back", "shoulders", "core"],
        "description": [
            "Start with feet hip-width apart, bar over midfoot",
            "Grip bar just outside knees with hook grip",
            "Set back flat, shoulders slightly over bar",
            "First pull: maintain back angle while pushing floor away",
            "Second pull: explosively extend hips and knees",
            "Keep bar close to body throughout movement",
            "Pull under bar while keeping elbows high",
            "Receive bar in partial squat position",
            "Stand to full extension"
        ]
    },
    "Wall Ball": {
        "tips": [
            "Drive through heels while opening hips",
            "Keep elbows in tight",
            "Time catch in quarter-squat position"
        ],
        "equipment": ["medicine ball", "wall"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=fpUD0mcFp_0",
        "crossfit_url": "https://www.crossfit.com/essentials/wall-ball",
        "body_part": ["legs", "shoulders", "core"],
        "description": [
            "Start with feet shoulder-width apart",
            "Hold medicine ball at chest",
            "Perform full depth squat",
            "Drive explosively through heels",
            "Extend hips, knees, and ankles",
            "Project ball upward to target",
            "Catch ball in quarter squat position",
            "Immediately begin next rep"
        ]
    },
    "Deadlift": {
        "tips": [
            "Keep bar close to shins",
            "Create tension before initiating pull",
            "Drive through heels"
        ],
        "equipment": ["barbell", "plates"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=op9kVnSso6Q",
        "crossfit_url": "https://www.crossfit.com/essentials/deadlift",
        "body_part": ["back", "legs", "core"],
        "description": [
            "Stand with feet hip-width apart",
            "Bar over midfoot, grip just outside legs",
            "Hinge at hips to grasp bar",
            "Chest up, back flat",
            "Create tension in hamstrings",
            "Drive through heels",
            "Keep bar close to body",
            "Stand to full extension"
        ]
    },
    "Overhead Squat": {
        "tips": [
            "Maintain active shoulders",
            "Keep bar behind head plane",
            "Push knees out while staying vertical"
        ],
        "equipment": ["barbell", "plates"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=RD_vUnqwqqI",
        "crossfit_url": "https://www.crossfit.com/essentials/overhead-squat",
        "body_part": ["legs", "shoulders", "core"],
        "description": [
            "Start with bar overhead, slightly behind head",
            "Wide grip, feet shoulder width",
            "Break at hips and knees simultaneously",
            "Keep torso vertical throughout",
            "Descend until hip crease below knee",
            "Drive through heels while maintaining position",
            "Stand to full extension"
        ]
    },
    "Back Squat": {
        "tips": [
            "Create tight bar position on upper back",
            "Break hips and knees together",
            "Drive knees out during movement"
        ],
        "equipment": ["barbell", "plates", "rack"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=ultWZbUMPL8",
        "crossfit_url": "https://www.crossfit.com/essentials/back-squat",
        "body_part": ["legs", "core", "back"],
        "description": [
            "Position bar on upper back (not neck)",
            "Grip outside shoulders, elbows down",
            "Feet shoulder width, toes slightly out",
            "Break at hips and knees together",
            "Keep chest up, core tight",
            "Descend until hip crease below knee",
            "Push through heels to stand"
        ]
    },
    "Rope Climb": {
        "tips": [
            "Use J-hook foot position",
            "Keep arms straight when resetting",
            "Control descent with legs"
        ],
        "equipment": ["climbing rope"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=AD0uN4r1F64",
        "crossfit_url": "https://www.crossfit.com/essentials/rope-climb",
        "body_part": ["grip", "back", "legs"],
        "description": [
            "Jump to grip rope at highest point",
            "Wrap rope around leg in J-hook",
            "Pinch rope between feet",
            "Stand up through legs",
            "Reach up and regrasp higher",
            "Control descent using same technique"
        ]
    },
    "Pistol": {
        "tips": [
            "Keep non-working leg straight",
            "Maintain upright torso",
            "Drive through full foot"
        ],
        "equipment": [],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=qDcniqddTeE",
        "crossfit_url": "https://www.crossfit.com/essentials/pistol",
        "body_part": ["legs", "core", "balance"],
        "description": [
            "Stand on one leg, other extended forward",
            "Keep non-working leg straight",
            "Break at hip to descend",
            "Keep torso upright",
            "Touch hamstring to calf",
            "Drive through foot to stand"
        ]
    },
    "Ring Dip": {
        "tips": [
            "Keep rings turned out at top",
            "Maintain hollow body",
            "Control descent with engaged shoulders"
        ],
        "equipment": ["rings"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=Npf7dJTz_yo",
        "crossfit_url": "",
        "body_part": ["shoulders", "chest", "triceps"],
        "description": [
            "Start in support position",
            "Turn rings slightly out",
            "Keep body hollow and tight",
            "Lower with control",
            "Bottom at 90-degree elbow bend",
            "Press back to support",
            "Turn rings out at top"
        ]
    },
    "GHD Sit-Up": {
        "tips": [
            "Control extension throughout",
            "Touch ground with straight arms",
            "Use hip flexors to return"
        ],
        "equipment": ["GHD machine"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=1pbZ8mX2D88",
        "crossfit_url": "https://www.crossfit.com/essentials/ghd-situp",
        "body_part": ["core", "hip flexors", "back"],
        "description": [
            "Position feet in plates, knees bent",
            "Hips just off front pad",
            "Start torso vertical",
            "Lower back with control",
            "Touch ground behind head",
            "Return to vertical with hip flexors"
        ]
    },
    "Kettlebell Swing": {
        "tips": [
            "Hinge at hips not squat",
            "Generate power from hips",
            "Keep arms relaxed"
        ],
        "equipment": ["kettlebell"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=vdezTMulJ-k",
        "crossfit_url": "https://www.crossfit.com/essentials/kettlebell-swing",
        "body_part": ["posterior chain", "core", "shoulders"],
        "description": [
            "Start with kettlebell in front",
            "Hinge at hips to grasp handle",
            "Pull kettlebell back between legs",
            "Keep back flat, arms straight",
            "Drive hips forward explosively",
            "Let kettlebell float to shoulder height",
            "Guide back between legs"
        ]
    },
    "Box Jump": {
        "tips": [
            "Jump from athletic stance",
            "Land softly with bent knees",
            "Step down to protect joints"
        ],
        "equipment": ["box"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=52r_Ul5k03g",
        "crossfit_url": "https://www.crossfit.com/essentials/box-jump",
        "body_part": ["legs", "power", "coordination"],
        "description": [
            "Stand facing box",
            "Load hips and swing arms back",
            "Drive arms up while jumping",
            "Pull knees toward chest",
            "Land softly on box",
            "Stand to full extension",
            "Step down controlled"
        ]
    },
    "Devil Press": {
        "tips": [
            "Control dumbbells on descent",
            "Generate power from hips",
            "Lock out overhead with feet together"
        ],
        "equipment": ["dumbbells"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=r3Ic8JSCv84",
        "crossfit_url": "",
        "body_part": ["full body", "shoulders", "legs"],
        "description": [
            "Start with dumbbells on ground",
            "Perform burpee with hands on dumbbells",
            "Jump feet forward to dumbbells",
            "Clean dumbbells to shoulders",
            "Press or snatch overhead",
            "Return to ground for next rep"
        ]
    },
    "Front Squat": {
        "tips": ["Keep elbows high", "Maintain upright torso", "Drive knees out"],
        "equipment": ["barbell", "plates", "rack"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=uYumuL_G_V0",
        "crossfit_url": "https://www.crossfit.com/essentials/front-squat",
        "body_part": ["legs", "core", "upper back"],
        "description": [
            "Position bar in front rack, elbows high",
            "Feet shoulder width, toes slightly out",
            "Break at hips and knees together",
            "Keep torso vertical throughout",
            "Descend until hip crease below knee",
            "Drive through heels to stand"
        ]
    },
    "Push Press": {
        "tips": ["Generate power from legs", "Keep bar close to face", "Time arm extension"],
        "equipment": ["barbell", "plates"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=iaBVSJm78ko",
        "crossfit_url": "https://www.crossfit.com/essentials/push-press",
        "body_part": ["shoulders", "legs", "core"],
        "description": [
            "Start in front rack position",
            "Quick dip by bending knees",
            "Drive explosively through legs",
            "Press bar overhead as hips extend",
            "Lock out arms at top",
            "Return to rack position"
        ]
    },
    "Hang Power Clean": {
        "tips": ["Start at hip crease", "Maintain hook grip", "Aggressive hip extension"],
        "equipment": ["barbell", "plates"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=_iUFG1-H7d0",
        "crossfit_url": "https://www.crossfit.com/essentials/hang-power-clean",
        "body_part": ["legs", "back", "shoulders"],
        "description": [
            "Start with bar at hip crease",
            "Hook grip outside knees",
            "Push hips back slightly",
            "Explosively extend hips and knees",
            "Pull elbows high and fast",
            "Receive in quarter squat",
            "Stand to full extension"
        ]
    },
    "Burpee": {
        "tips": ["Keep core tight", "Minimize ground contact", "Jump feet together"],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=auBLPXO8Fww",
        "crossfit_url": "https://www.crossfit.com/essentials/burpee",
        "body_part": ["full body"],
        "description": [
            "Start standing, drop to ground",
            "Land in plank position",
            "Lower chest to ground",
            "Jump feet to hands",
            "Jump up with hands overhead",
            "Land ready to repeat"
        ]
    },
    "Ring Row": {
        "tips": ["Keep body rigid", "Pull rings to chest", "Control descent"],
        "equipment": ["rings"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=dL5oHKcvO4k",
        "crossfit_url": "",
        "body_part": ["back", "biceps", "core"],
        "description": [
            "Position rings at appropriate height",
            "Grip rings palms facing",
            "Body straight heels to shoulders",
            "Pull rings to chest",
            "Maintain rigid body",
            "Control return to start"
        ]
    },
    "Muscle Ups": {
        "tips": ["Generate power from hollow-to-arch swing", "Keep false grip", "Stay close during transition"],
        "equipment": ["rings", "pull-up bar"],
        "expertise": 5,
        "demo_url": "https://www.youtube.com/watch?v=astSQRh1-i0",
        "crossfit_url": "",
        "body_part": ["shoulders", "chest", "back", "core"],
        "description": [
            "Start in dead hang with false grip",
            "Kip swing from hollow to arch",
            "Pull explosively to sternum",
            "Keep elbows close in transition",
            "Rotate wrists and drive elbows back",
            "Push to support position",
            "Lock out arms at top"
        ]
    },

    "Air Squat": {
        "tips": ["Keep weight in heels", "Push knees out", "Maintain upright torso"],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=C_VtOYc6j5c",
        "crossfit_url": "https://www.crossfit.com/essentials/air-squat",
        "body_part": ["legs", "core"],
        "description": [
            "Feet shoulder width apart",
            "Break at hips first",
            "Push knees out over toes",
            "Descend below parallel",
            "Drive through heels",
            "Stand to full extension"
        ]
    },
    "Clean": {
        "tips": ["Keep bar close", "Complete triple extension", "Fast elbows in catch"],
        "equipment": ["barbell", "plates"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=EKRiW9Yt3Ps",
        "crossfit_url": "https://www.crossfit.com/essentials/clean",
        "body_part": ["legs", "back", "shoulders"],
        "description": [
            "Bar over midfoot, hook grip",
            "First pull maintaining back angle",
            "Explosive hip extension",
            "Pull under with high elbows",
            "Receive in front squat",
            "Stand to completion"
        ]
    },
    "Dumbbell Snatch": {
        "tips": ["Keep dumbbell close", "Punch through at top", "Receive in partial squat"],
        "equipment": ["dumbbell"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=9520DJiFmvE",
        "crossfit_url": "",
        "body_part": ["legs", "shoulders", "core"],
        "description": [
            "Start between feet",
            "Pull dumbbell close to body",
            "Extend hips explosively",
            "Pull high while dropping under",
            "Punch hand through overhead",
            "Stand to completion"
        ]
    },
    "Turkish Get-Up": {
        "tips": ["Watch weight throughout", "Move deliberately", "Keep arm vertical"],
        "equipment": ["kettlebell", "dumbbell"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=jFK8FOiLa_M",
        "crossfit_url": "",
        "body_part": ["full body", "shoulders", "core"],
        "description": [
            "Start lying down, weight pressed up",
            "Roll to elbow, then hand",
            "Sweep leg through to kneel",
            "Stand while keeping arm locked",
            "Reverse movement to return"
        ]
    },
    "Power Snatch": {
        "tips": ["Bar close to body", "Complete extension", "Lock arms quickly"],
        "equipment": ["barbell", "plates"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=tuOiNeTvLJs",
        "crossfit_url": "https://www.crossfit.com/essentials/power-snatch",
        "body_part": ["legs", "shoulders", "back"],
        "description": [
            "Wide grip, bar over midfoot",
            "First pull maintaining back angle",
            "Explosive hip extension",
            "High pull while dropping under",
            "Receive overhead in partial squat",
            "Stand to completion"
        ]
    },
    "Kettlebell Clean": {
        "tips": ["Keep bell close", "Thread arm through handle", "Soft catch in rack"],
        "equipment": ["kettlebell"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=C0B1SrcGAIA",
        "crossfit_url": "",
        "body_part": ["legs", "shoulders", "core"],
        "description": [
            "Start between feet",
            "Hinge at hips to grasp",
            "Pull close to body",
            "Thread arm as bell rises",
            "Guide to rack position",
            "Stand to completion"
        ]
    },
    "Legless Rope Climb": {
        "tips": ["Generate power from upper body", "Efficient grip changes", "Control descent"],
        "equipment": ["climbing rope"],
        "expertise": 5,
        "demo_url": "https://www.youtube.com/watch?v=nkr6mh_OUzs",
        "crossfit_url": "",
        "body_part": ["grip", "back", "shoulders"],
        "description": [
            "Hang from rope with strong grip",
            "Pull explosively with arms",
            "Alternate hands climbing up",
            "Keep core tight throughout",
            "Control descent speed",
            "Use opposing grip down"
        ]
    },
    "Overhead Walking Lunge": {
        "tips": ["Lock arms overhead", "Vertical torso", "Control balance"],
        "equipment": ["barbell", "plates", "dumbbells", "kettlebell"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=1HxU9OIJaSo",
        "crossfit_url": "",
        "body_part": ["legs", "shoulders", "core"],
        "description": [
            "Weight locked overhead",
            "Step forward to lunge",
            "Back knee to ground",
            "Drive through front heel",
            "Maintain active shoulders",
            "Alternate legs each step"
        ]
    },
    "Ring L-Sit": {
        "tips": ["Push rings down", "Straight legs", "Hollow body"],
        "equipment": ["rings"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=c_lkWvh6hxE",
        "crossfit_url": "",
        "body_part": ["core", "shoulders", "hip flexors"],
        "description": [
            "Support on rings, arms straight",
            "Push rings down and back",
            "Lift legs parallel to ground",
            "Point toes, legs together",
            "Hold position",
            "Maintain shoulder depression"
        ]
    },
    "Deficit Handstand Push-up": {
        "tips": ["Control descent below hands", "Maintain hollow", "Explosive press"],
        "equipment": ["wall", "plates", "blocks"],
        "expertise": 5,
        "demo_url": "https://www.youtube.com/watch?v=h7uqWZFEBAg",
        "crossfit_url": "",
        "body_part": ["shoulders", "triceps", "core"],
        "description": [
            "Set up deficit with plates",
            "Kick up to handstand",
            "Lower head below hands",
            "Push explosively up",
            "Lock out arms",
            "Control each rep"
        ]
    },
    "Front Scale": {
        "tips": ["Balance on one leg", "Raise other leg parallel", "Keep standing leg straight"],
        "equipment": [],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=RQF1ZNfvKF4",
        "crossfit_url": "",
        "body_part": ["balance", "hamstrings", "core"],
        "description": [
            "Stand on one leg",
            "Hinge at hips",
            "Raise back leg",
            "Form T-position",
            "Hold position",
            "Return to standing"
        ]
    },
    "Dragon Flag": {
        "tips": ["Keep body straight", "Control lowering", "Maintain shoulder contact"],
        "equipment": ["bench"],
        "expertise": 5,
        "demo_url": "https://www.youtube.com/watch?v=moyFIvRrS0s",
        "crossfit_url": "",
        "body_part": ["core", "shoulders", "back"],
        "description": [
            "Lie on bench, grip behind head",
            "Press shoulders down",
            "Lift legs and hips",
            "Keep body straight",
            "Lower with control",
            "Return to start"
        ]
    },
    "Running": {
        "tips": ["Land midfoot", "Upright posture", "Relaxed arms"],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=wCVSv7UxB2E",
        "crossfit_url": "https://www.crossfit.com/essentials/running",
        "body_part": ["legs", "cardio"],
        "description": [
            "Upright posture, slight lean",
            "Arms at 90 degrees",
            "Land midfoot under body",
            "Push off back foot",
            "Maintain steady rhythm",
            "Look ahead"
        ]
    },
    "Russian Kettlebell Swing": {
        "tips": ["Hinge at hips", "Flat back", "Shoulder height only"],
        "equipment": ["kettlebell"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=cKx8xE8jJZs",
        "crossfit_url": "https://www.crossfit.com/essentials/kettlebell-swing",
        "body_part": ["posterior chain", "core", "shoulders"],
        "description": [
            "Stand with feet shoulder-width",
            "Hinge to grasp kettlebell",
            "Hike between legs",
            "Thrust hips forward",
            "Let bell float to shoulders",
            "Control descent"
        ]
    },
    "Medicine Ball Clean": {
        "tips": ["Keep ball close", "Use hip drive", "Catch in squat"],
        "equipment": ["medicine ball"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=kTn8RdX9OzQ",
        "crossfit_url": "https://www.crossfit.com/essentials/med-ball-clean",
        "body_part": ["full body"],
        "description": [
            "Ball between feet",
            "Clean grip on ball",
            "Pull close to body",
            "Drive hips to elevate",
            "Drop under to catch",
            "Stand to complete"
        ]
    },
    "Row": {
        "tips": ["Drive with legs first", "Keep core engaged", "Sequence: legs-back-arms"],
        "equipment": ["rowing machine"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=3CfUxYqz1Ws",
        "crossfit_url": "https://www.crossfit.com/essentials/rowing",
        "body_part": ["full body", "cardio"],
        "description": [
            "Catch position, shins vertical",
            "Drive legs while arms straight",
            "Lean back slightly",
            "Pull handle to ribs",
            "Return arms-body-legs",
            "Control slide return"
        ]
    },
    "Sumo Deadlift High Pull": {
        "tips": ["Wide stance, toes out", "Keep chest up", "Pull elbows high"],
        "equipment": ["barbell", "plates"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=gh55vVlCABU",
        "crossfit_url": "https://www.crossfit.com/essentials/sumo-deadlift-high-pull",
        "body_part": ["legs", "back", "shoulders"],
        "description": [
            "Wide stance, toes out",
            "Grasp bar inside legs",
            "Drive through heels",
            "Extend hips and knees",
            "Pull elbows high",
            "Control descent"
        ]
    },
    "Box Step-up": {
        "tips": ["Full foot on box", "Drive through heel", "Control step down"],
        "equipment": ["box"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=B-W8C9B_Dws",
        "crossfit_url": "https://www.crossfit.com/essentials/box-step-up",
        "body_part": ["legs", "balance"],
        "description": [
            "Face box of appropriate height",
            "Place foot fully on box",
            "Drive through heel",
            "Stand to full extension",
            "Step down controlled",
            "Alternate legs"
        ]
    },
    "Hollow Rock": {
        "tips": ["Press lower back down", "Straight legs", "Consistent rhythm"],
        "equipment": [],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=p7j02V1fIzk",
        "crossfit_url": "https://www.crossfit.com/essentials/hollow-rock",
        "body_part": ["core", "hip flexors"],
        "description": [
            "Lie back, arms overhead",
            "Press lower back to ground",
            "Lift shoulders and legs",
            "Rock from shoulders to hips",
            "Maintain hollow position",
            "Keep movements small"
        ]
    },
    "Push Jerk": {
        "tips": ["Quick dip", "Drive through legs", "Lock out overhead"],
        "equipment": ["barbell", "plates"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=2zj7Y7g5rXk",
        "crossfit_url": "https://www.crossfit.com/essentials/push-jerk",
        "body_part": ["shoulders", "legs", "core"],
        "description": [
            "Start with barbell in front rack position",
            "Feet shoulder width apart",
            "Quick dip by bending knees",
            "Drive explosively through legs",
            "Press bar overhead as hips extend",
            "Lock out arms at top",
            "Return to front rack position"
        ]
    },
    "Knees-to-Elbows": {
        "tips": ["Generate shoulder swing", "Keep core tight", "Touch knees to elbows"],
        "equipment": ["pull-up bar"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=_03pCKOv4l4",
        "crossfit_url": "https://www.crossfit.com/essentials/knees-to-elbows",
        "body_part": ["core", "grip", "coordination"],
        "description": [
            "Hang from pull-up bar",
            "Start with hollow body position",
            "Generate swing from shoulders",
            "Keep arms straight",
            "Bring knees to touch elbows",
            "Return to hollow position",
            "Maintain rhythm between reps"
        ]
    },
    "Split Jerk": {
        "tips": ["Drive through legs", "Fast split under bar", "Vertical bar path"],
        "equipment": ["barbell", "plates"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=GR39TGeH0Ck",
        "crossfit_url": "https://www.crossfit.com/essentials/split-jerk",
        "body_part": ["legs", "shoulders", "core"],
        "description": [
            "Start with bar in front rack",
            "Quick dip with vertical torso",
            "Drive bar up with legs",
            "Split feet front/back",
            "Lock arms overhead",
            "Return feet to center",
            "Control bar back to rack"
        ]
    },

    "Power Jerk": {
        "tips": ["Quick dip and drive", "Land in partial squat", "Active shoulders"],
        "equipment": ["barbell", "plates"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=WxDaaFVXFyU",
        "crossfit_url": "https://www.crossfit.com/essentials/power-jerk",
        "body_part": ["legs", "shoulders", "core"],
        "description": [
            "Bar in front rack position",
            "Shallow dip with knees",
            "Explosive drive upward",
            "Press under bar",
            "Receive in quarter squat",
            "Stand to full extension",
            "Return to rack position"
        ]
    },

    "Hang Clean": {
        "tips": ["Start at hip crease", "Keep bar close", "Fast elbows"],
        "equipment": ["barbell", "plates"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=WCdhjfg7fv4",
        "crossfit_url": "https://www.crossfit.com/essentials/hang-clean",
        "body_part": ["legs", "back", "shoulders"],
        "description": [
            "Start with bar at hips",
            "Slight knee bend",
            "Push hips back",
            "Explosive hip extension",
            "Pull under with elbows high",
            "Receive in front squat",
            "Stand to completion"
        ]
    },

    "Hang Clean & Jerk": {
        "tips": ["Complete clean before jerk", "Stay connected to bar", "Time transitions"],
        "equipment": ["barbell", "plates"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=WCdhjfg7fv4",
        "crossfit_url": "",
        "body_part": ["full body"],
        "description": [
            "Begin with bar at hips",
            "Perform hang clean",
            "Stand fully from clean",
            "Reset for jerk",
            "Execute chosen jerk style",
            "Return bar to hang position",
            "Maintain control throughout"
        ]
    },

    "Hang Snatch": {
        "tips": ["Maintain hook grip", "Complete extension", "Fast turnover"],
        "equipment": ["barbell", "plates"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=9xQp2sldyts",
        "crossfit_url": "",
        "body_part": ["full body", "shoulders", "legs"],
        "description": [
            "Start with bar at hips",
            "Wide snatch grip",
            "Push hips back slightly",
            "Explosive hip drive",
            "Pull under while keeping arms straight",
            "Receive in overhead squat",
            "Stand to completion"
        ]
    },

    "Squat Snatch": {
        "tips": ["Keep bar close", "Complete pull before dropping", "Stable overhead position"],
        "equipment": ["barbell", "plates"],
        "expertise": 5,
        "demo_url": "https://www.youtube.com/watch?v=9xQp2sldyts",
        "crossfit_url": "",
        "body_part": ["full body", "shoulders", "legs"],
        "description": [
            "Start with wide grip",
            "First pull to power position",
            "Complete triple extension",
            "Pull under aggressively",
            "Receive in full squat",
            "Stand with bar overhead",
            "Maintain active shoulders"
        ]
    },

    "High Pull": {
        "tips": ["Power from hips", "Keep elbows high", "Bar close to body"],
        "equipment": ["barbell", "plates"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=gh55vVlCABU",
        "crossfit_url": "",
        "body_part": ["back", "shoulders", "legs"],
        "description": [
            "Start over midfoot",
            "Pull bar from ground",
            "Accelerate with hips",
            "Shrug shoulders",
            "Pull elbows high",
            "Control return to start",
            "Maintain back position"
        ]
    },

    "Strict Pull-up": {
        "tips": ["Start from dead hang", "Pull shoulder blades down", "Control descent"],
        "equipment": ["pull-up bar"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=eGo4IYlbE5g",
        "crossfit_url": "",
        "body_part": ["back", "biceps", "shoulders"],
        "description": [
            "Hang with full arm extension",
            "Engage shoulder blades",
            "Pull chin over bar",
            "Keep core tight",
            "Lower with control",
            "Return to dead hang",
            "Maintain body control"
        ]
    },

    "Butterfly Pull-up": {
        "tips": ["Time the kip perfectly", "Keep shoulders active", "Maintain rhythm"],
        "equipment": ["pull-up bar"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=OenVG15QMj8",
        "crossfit_url": "",
        "body_part": ["back", "shoulders", "core"],
        "description": [
            "Start with shoulders engaged",
            "Generate circular motion",
            "Pull chest to bar",
            "Drive shoulders forward",
            "Return through hollow",
            "Maintain continuous motion",
            "Keep consistent rhythm"
        ]
    },

    "Strict HSPU": {
        "tips": ["Lock core tight", "Press evenly", "Control descent"],
        "equipment": ["wall"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=0wDEO6shVjc",
        "crossfit_url": "",
        "body_part": ["shoulders", "triceps", "core"],
        "description": [
            "Kick up to handstand",
            "Set shoulders firmly",
            "Lower head to ground",
            "Press back to start",
            "Maintain body alignment",
            "Keep elbows in",
            "Full lockout at top"
        ]
    },

    "Butterfly C2B": {
        "tips": ["Aggressive hip drive", "Pull high", "Time the touch"],
        "equipment": ["pull-up bar"],
        "expertise": 5,
        "demo_url": "https://www.youtube.com/watch?v=p9Stan68FYM",
        "crossfit_url": "",
        "body_part": ["back", "chest", "shoulders"],
        "description": [
            "Begin with shoulders active",
            "Generate powerful kip",
            "Pull aggressively high",
            "Touch chest to bar",
            "Return through hollow",
            "Maintain butterfly rhythm",
            "Keep consistent contact point"
        ]
    },

    "L-sit": {
        "tips": ["Press shoulders down", "Point toes", "Engage core"],
        "equipment": ["parallettes", "rings"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=c_lkWvh6hxE",
        "crossfit_url": "",
        "body_part": ["core", "hip flexors", "shoulders"],
        "description": [
            "Support on chosen apparatus",
            "Lock arms straight",
            "Lift legs parallel to ground",
            "Keep legs together",
            "Hold position",
            "Maintain shoulder depression",
            "Keep core engaged"
        ]
    },

    "Ring Support Hold": {
        "tips": ["Turn rings out", "Lock arms", "Stay tight"],
        "equipment": ["rings"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=Npf7dJTz_yo",
        "crossfit_url": "",
        "body_part": ["shoulders", "core", "stability"],
        "description": [
            "Jump to support position",
            "Lock arms straight",
            "Turn rings out",
            "Keep shoulders down",
            "Maintain hollow body",
            "Hold prescribed time",
            "Lower with control"
        ]
    },

    "Skin the Cat": {
        "tips": ["Start slow", "Keep arms straight", "Control rotation"],
        "equipment": ["rings"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=zQFyIWak8K8",
        "crossfit_url": "",
        "body_part": ["shoulders", "back", "core"],
        "description": [
            "Hang from rings",
            "Lift legs overhead",
            "Continue rotation back",
            "Straighten body through",
            "Return same path",
            "Maintain shoulder control",
            "Keep arms locked"
        ]
    },

    "Muscle Snatch": {
        "tips": ["Stay over bar", "Pull high", "Fast turnover"],
        "equipment": ["barbell", "plates"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=9xQp2sldyts",
        "crossfit_url": "",
        "body_part": ["shoulders", "back", "legs"],
        "description": [
            "Take wide grip",
            "Start over midfoot",
            "Pull bar close to body",
            "High pull to shoulders",
            "Punch under bar",
            "Lock out overhead",
            "Control return to start"
        ]
    },

    "V-up": {
        "tips": ["Touch hands to feet", "Keep legs straight", "Control movement"],
        "equipment": [],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=7UVgs1y6L-Q",
        "crossfit_url": "",
        "body_part": ["core", "hip flexors"],
        "description": [
            "Lie on back",
            "Arms overhead",
            "Lift legs and torso",
            "Touch hands to feet",
            "Lower with control",
            "Keep legs straight",
            "Maintain tension"
        ]
    },

    "Strict T2B": {
        "tips": ["Start from dead hang", "Pike body", "Control descent"],
        "equipment": ["pull-up bar"],
        "expertise": 4,
        "demo_url": "https://www.youtube.com/watch?v=_03pCKOv4l4",
        "crossfit_url": "",
        "body_part": ["core", "hip flexors", "grip"],
        "description": [
            "Hang from pull-up bar",
            "Keep arms straight",
            "Pike at hips",
            "Lift toes to touch bar",
            "Lower with control",
            "Return to dead hang",
            "Maintain strict form"
        ]
    },

    "Superman Hold": {
        "tips": ["Lift limbs high", "Keep neck neutral", "Squeeze glutes"],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=z6PJMT2y8GQ",
        "crossfit_url": "",
        "body_part": ["back", "glutes", "shoulders"],
        "description": [
            "Lie face down",
            "Arms extended forward",
            "Lift arms and legs",
            "Hold position",
            "Keep neck aligned",
            "Maintain elevation",
            "Breathe normally"
        ]
    },

    "Ab Mat Sit-up": {
        "tips": ["Use hip flexors", "Touch ground overhead", "Control descent"],
        "equipment": ["ab mat"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=_HDZODOx7Zw",
        "crossfit_url": "",
        "body_part": ["core", "hip flexors"],
        "description": [
            "Position ab mat under lower back",
            "Feet anchored",
            "Arms overhead",
            "Sit up completely",
            "Touch ground behind head",
            "Return controlled",
            "Maintain rhythm"
        ]
    },

    "Back Extension": {
        "tips": ["Squeeze glutes", "Keep neck neutral", "Control movement"],
        "equipment": ["GHD machine"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=9xQp2sldyts",
        "crossfit_url": "",
        "body_part": ["back", "glutes"],
        "description": [
            "Position on GHD",
            "Hinge at hips",
            "Lower torso down",
            "Extend back up",
            "Squeeze glutes at top",
            "Maintain alignment",
            "Control tempo"
        ]
    },

    "Front Rack Carry": {
        "tips": ["Keep elbows high", "Brace core", "Maintain posture"],
        "equipment": ["dumbbells", "kettlebells"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=2qIVRgE5yRE",
        "crossfit_url": "",
        "body_part": ["core", "shoulders", "legs"],
        "description": [
            "Clean weights to shoulders",
            "Elbows high and forward",
            "Stand tall",
            "Walk prescribed distance",
            "Maintain rack position",
            "Keep core tight",
            "Control breathing"
        ]
    },

    "Farmers Carry": {
        "tips": ["Keep shoulders back", "Stand tall", "Maintain grip"],
        "equipment": ["dumbbells", "kettlebells"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=2qIVRgE5yRE",
        "crossfit_url": "",
        "body_part": ["grip", "core", "legs"],
        "description": [
            "Grasp weights at sides",
            "Stand tall",
            "Walk prescribed distance",
            "Keep shoulders packed",
            "Maintain posture",
            "Control pace",
            "Breathe steadily"
        ]
    },
    "Alternating Lunges": {
        "tips": [
            "Keep front knee tracked over ankle",
            "Maintain upright torso",
            "Touch back knee lightly to ground"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=L8fvypPrzzs",
        "body_part": ["legs", "balance", "core"],
        "description": [
            "Stand with feet hip-width apart",
            "Step forward with one leg",
            "Lower back knee toward ground",
            "Keep front knee over ankle",
            "Drive through front heel to stand",
            "Return to starting position",
            "Alternate legs each rep"
        ]
    },

    "Bear Crawl": {
        "tips": [
            "Keep hips low and level",
            "Move opposite hand and foot",
            "Maintain neutral spine"
        ],
        "equipment": [],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=bfT5TaRFKQw",
        "body_part": ["core", "shoulders", "coordination"],
        "description": [
            "Start on hands and knees",
            "Lift knees slightly off ground",
            "Move forward using opposite limbs",
            "Keep back flat and core engaged",
            "Maintain hip height throughout",
            "Take small, controlled steps",
            "Look slightly ahead of hands"
        ]
    },

    "Scap Pull-up": {
        "tips": [
            "Keep arms straight",
            "Focus on shoulder blade movement",
            "Control both up and down portions"
        ],
        "equipment": ["pull-up bar"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=icD6a_JcCbQ",
        "body_part": ["shoulders", "back"],
        "description": [
            "Hang from pull-up bar with straight arms",
            "Pull shoulder blades down and together",
            "Keep arms completely straight",
            "Lift body slightly with shoulder movement",
            "Lower with control",
            "Maintain steady rhythm",
            "Focus on shoulder blade engagement"
        ]
    },

    "Samson Stretch": {
        "tips": [
            "Keep front knee over ankle",
            "Reach arms overhead",
            "Push hips forward"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=U1zS6RYh_BY",
        "body_part": ["hip flexors", "shoulders", "core"],
        "description": [
            "Start in lunge position",
            "Back knee on ground",
            "Reach arms overhead",
            "Push hips forward gently",
            "Keep chest up and core engaged",
            "Hold position for prescribed time",
            "Breathe deeply throughout stretch"
        ]
    },

    "Inchworm": {
        "tips": [
            "Keep legs as straight as possible",
            "Walk hands out slowly",
            "Maintain core engagement"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=ZY2ji_Ho0dA",
        "body_part": ["core", "shoulders", "hamstrings"],
        "description": [
            "Stand with feet hip-width apart",
            "Bend forward and touch ground",
            "Walk hands forward to plank",
            "Keep legs straight if possible",
            "Walk feet up to hands",
            "Return to standing",
            "Maintain controlled movement"
        ]
    },

    "Dumbbell Farmers Carry": {
        "tips": [
            "Keep shoulders back and down",
            "Maintain neutral spine",
            "Walk with controlled steps"
        ],
        "equipment": ["dumbbells"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=rt17lmnaLSM",
        "body_part": ["grip", "core", "traps"],
        "description": [
            "Hold dumbbells at sides",
            "Stand tall with chest up",
            "Engage core and pack shoulders",
            "Walk prescribed distance",
            "Take controlled steps",
            "Maintain posture throughout",
            "Keep breathing steady"
        ]
    },

    "Plank Hold": {
        "tips": [
            "Maintain straight line from head to heels",
            "Keep core tight",
            "Don't let hips sag"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=ASdvN_XEl_c",
        "body_part": ["core", "shoulders"],
        "description": [
            "Start on forearms and toes",
            "Align body in straight line",
            "Engage core muscles",
            "Keep shoulders over elbows",
            "Hold position for prescribed time",
            "Maintain steady breathing",
            "Keep glutes engaged"
        ]
    },

    "Mountain Climbers": {
        "tips": [
            "Keep hips low",
            "Drive knees toward chest",
            "Maintain plank position"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=nmwgirgXLYM",
        "body_part": ["core", "shoulders", "cardio"],
        "description": [
            "Start in plank position",
            "Drive one knee toward chest",
            "Quickly alternate legs",
            "Keep shoulders stable",
            "Maintain hip position",
            "Keep core engaged",
            "Control breathing pattern"
        ]
    },

    "Plate Ground-to-Overhead": {
        "tips": [
            "Keep plate close to body",
            "Use hip drive",
            "Lock out arms overhead"
        ],
        "equipment": ["weight plate"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=6l2Iu_jV6Ho",
        "body_part": ["full body"],
        "description": [
            "Start with plate on ground",
            "Hinge to grasp plate",
            "Pull plate close to body",
            "Drive through hips",
            "Press plate overhead",
            "Lock out arms completely",
            "Return plate to ground controlled"
        ]
    },

    "Scorpion Stretch": {
        "tips": [
            "Keep shoulders on ground",
            "Move slowly and controlled",
            "Focus on hip mobility"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=0HTXQdxYS2g",
        "body_part": ["spine", "hips", "shoulders"],
        "description": [
            "Lie face down",
            "Bend one knee",
            "Reach foot across body",
            "Keep shoulders down",
            "Hold stretch position",
            "Return to start",
            "Alternate sides"
        ]
    },

    "Up-downs": {
        "tips": [
            "Move quickly but controlled",
            "Maintain plank position",
            "Keep core engaged"
        ],
        "equipment": [],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=0HTXQdxYS2g",
        "body_part": ["shoulders", "core", "cardio"],
        "description": [
            "Start in plank position",
            "Lower to forearms one arm at time",
            "Push back up to hands one arm at time",
            "Maintain plank position throughout",
            "Alternate leading arm",
            "Keep hips stable",
            "Control movement speed"
        ]
    },

    "Single Leg V-ups": {
        "tips": [
            "Keep non-working leg on ground",
            "Reach for toes",
            "Control the lowering"
        ],
        "equipment": [],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=0HTXQdxYS2g",
        "body_part": ["core", "hip flexors"],
        "description": [
            "Lie on back",
            "One leg extended up",
            "Arms overhead",
            "Lift torso and reach for foot",
            "Keep other leg on ground",
            "Lower with control",
            "Alternate legs"
        ]
    },

    "Spiderman Stretch": {
        "tips": [
            "Keep back leg straight",
            "Drive hip toward ground",
            "Maintain straight front leg"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=0HTXQdxYS2g",
        "body_part": ["hips", "groin", "mobility"],
        "description": [
            "Start in push-up position",
            "Step one foot outside same-side hand",
            "Lower hip toward ground",
            "Keep rear leg straight",
            "Hold stretch position",
            "Return to start",
            "Alternate sides"
        ]
    },

    "Dumbbell Overhead Carry": {
        "tips": [
            "Lock arms fully",
            "Keep core tight",
            "Walk with control"
        ],
        "equipment": ["dumbbells"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=0HTXQdxYS2g",
        "body_part": ["shoulders", "core", "stability"],
        "description": [
            "Clean dumbbells to shoulders",
            "Press overhead with locked arms",
            "Walk prescribed distance",
            "Maintain stable overhead position",
            "Keep core engaged",
            "Control breathing",
            "Take measured steps"
        ]
    },

    "Hand Release Push-ups": {
        "tips": [
            "Full chest contact with ground",
            "Lift hands completely",
            "Push explosively"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=0HTXQdxYS2g",
        "body_part": ["chest", "shoulders", "triceps"],
        "description": [
            "Start in push-up position",
            "Lower chest to ground",
            "Lift hands off ground briefly",
            "Replace hands",
            "Push back to start",
            "Maintain plank position",
            "Keep core engaged"
        ]
    },

    "Walking Lunges": {
        "tips": [
            "Keep torso upright",
            "Step naturally",
            "Land heel to toe"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=0HTXQdxYS2g",
        "body_part": ["legs", "balance", "core"],
        "description": [
            "Stand tall",
            "Step forward into lunge",
            "Lower back knee toward ground",
            "Drive through front heel",
            "Step through to next lunge",
            "Maintain upright posture",
            "Continue alternating legs"
        ]
    },

    "Good Mornings": {
        "tips": [
            "Hinge at hips",
            "Keep back straight",
            "Push hips back"
        ],
        "equipment": [],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=0HTXQdxYS2g",
        "body_part": ["hamstrings", "lower back", "core"],
        "description": [
            "Stand with feet hip-width",
            "Place hands behind head",
            "Push hips back",
            "Keep back straight",
            "Lower torso forward",
            "Feel stretch in hamstrings",
            "Return to standing"
        ]
    },

    "Leg Swings": {
        "tips": [
            "Start small and increase range",
            "Keep standing leg stable",
            "Maintain balance"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=0HTXQdxYS2g",
        "body_part": ["hips", "mobility"],
        "description": [
            "Stand on one leg",
            "Hold support if needed",
            "Swing other leg forward and back",
            "Keep movement controlled",
            "Gradually increase range",
            "Maintain upright posture",
            "Switch legs"
        ]
    },

    "Shuttle Runs": {
        "tips": [
            "Touch line each turn",
            "Stay low when turning",
            "Accelerate out of turns"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=0HTXQdxYS2g",
        "body_part": ["legs", "cardio", "agility"],
        "description": [
            "Start at first marker",
            "Sprint to second marker",
            "Touch ground or line",
            "Turn quickly",
            "Sprint back to start",
            "Touch starting line",
            "Repeat for prescribed distance"
        ]
    },

    "Toy Soldiers": {
        "tips": [
            "Keep legs straight",
            "Reach opposite hand to foot",
            "Stay controlled"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=0HTXQdxYS2g",
        "body_part": ["hamstrings", "mobility"],
        "description": [
            "Stand tall",
            "Kick one leg straight up",
            "Reach opposite hand to foot",
            "Keep support leg straight",
            "Return leg to ground",
            "Alternate sides",
            "Walk forward while performing"
        ]
    },

    "Dumbbell Romanian Deadlifts": {
        "tips": [
            "Keep back flat throughout movement",
            "Push hips back while lowering",
            "Maintain slight knee bend"
        ],
        "equipment": ["dumbbells"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=ws33X7ppKhM",
        "body_part": ["hamstrings", "back", "glutes"],
        "description": [
            "Start standing with dumbbells at sides",
            "Hinge at hips while pushing back",
            "Lower weights along legs",
            "Keep back flat throughout",
            "Feel stretch in hamstrings",
            "Drive hips forward to stand",
            "Squeeze glutes at top"
        ]
    },
    "Front Rack Lunge": {
        "tips": [
            "Keep elbows high in rack",
            "Maintain upright torso",
            "Control knee tracking"
        ],
        "equipment": ["barbell", "plates"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=f3WLs_HutLw",
        "body_part": ["legs", "core", "shoulders"],
        "description": [
            "Start with barbell in front rack",
            "Step forward into lunge",
            "Keep torso vertical",
            "Lower back knee toward ground",
            "Drive through front heel",
            "Return to starting position",
            "Maintain rack position throughout"
        ]
    },

    "Bar Facing Burpee": {
        "tips": [
            "Jump back to plank together",
            "Jump over bar with two feet",
            "Stay close to bar"
        ],
        "equipment": ["barbell"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=9_9yqdZ_eT4",
        "body_part": ["full body", "cardio"],
        "description": [
            "Start facing barbell",
            "Drop to ground for burpee",
            "Chest touches ground",
            "Jump feet back to hands",
            "Jump over barbell",
            "Land softly on other side",
            "Turn around and repeat"
        ]
    },

    "Kettlebell Front Rack": {
        "tips": [
            "Keep elbow tight to body",
            "Stack kettlebell on forearm",
            "Maintain upright posture"
        ],
        "equipment": ["kettlebell"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=0WW4kx9jV94",
        "body_part": ["shoulders", "core"],
        "description": [
            "Clean kettlebell to shoulder",
            "Elbow tight to ribs",
            "Stack bell on forearm",
            "Keep wrist straight",
            "Maintain vertical position",
            "Keep core engaged",
            "Control breathing pattern"
        ]
    },

    "Bent Over Rows": {
        "tips": [
            "Hinge at hips 45 degrees",
            "Pull elbows back",
            "Keep back flat"
        ],
        "equipment": ["barbell", "dumbbells"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=FWJR5Ve8bnQ",
        "body_part": ["back", "biceps"],
        "description": [
            "Hinge forward at hips",
            "Keep back flat",
            "Hold weight with straight arms",
            "Pull weight to lower ribs",
            "Squeeze shoulder blades",
            "Lower weight controlled",
            "Maintain hip hinge"
        ]
    },

    "Goblet Squats": {
        "tips": [
            "Hold weight close to chest",
            "Keep elbows between knees",
            "Maintain upright torso"
        ],
        "equipment": ["kettlebell", "dumbbell"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=MxsFDhcyFyE",
        "body_part": ["legs", "core"],
        "description": [
            "Hold weight at chest height",
            "Feet shoulder width apart",
            "Break at hips and knees",
            "Keep elbows inside knees",
            "Squat to full depth",
            "Drive through heels",
            "Stand to full extension"
        ]
    },

    "Wall Walk": {
        "tips": [
            "Keep core tight",
            "Take small steps up wall",
            "Control movement down"
        ],
        "equipment": ["wall"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=BvxZQH_KDqw",
        "body_part": ["shoulders", "core"],
        "description": [
            "Start in plank facing wall",
            "Walk feet up wall",
            "Walk hands toward wall",
            "Reach handstand position",
            "Walk hands away from wall",
            "Walk feet down controlled",
            "Return to plank"
        ]
    },

    "Kettlebell Deadlifts": {
        "tips": [
            "Keep kettlebell close",
            "Hinge at hips",
            "Drive through heels"
        ],
        "equipment": ["kettlebell"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=F4y7BqMX1mY",
        "body_part": ["legs", "back", "core"],
        "description": [
            "Place kettlebell between feet",
            "Hinge at hips to grasp",
            "Keep back flat",
            "Drive through heels",
            "Stand to full extension",
            "Return bell to ground",
            "Maintain neutral spine"
        ]
    },

    "PVC Pass-throughs": {
        "tips": [
            "Keep arms straight",
            "Start wide and narrow grip",
            "Control movement speed"
        ],
        "equipment": ["PVC pipe"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=W5HP7taocu0",
        "body_part": ["shoulders", "mobility"],
        "description": [
            "Hold PVC with wide grip",
            "Keep arms straight",
            "Pass pipe from front to back",
            "Maintain straight arms",
            "Return to front",
            "Control movement speed",
            "Progress to narrower grip"
        ]
    },

    "Single Unders": {
        "tips": [
            "Use wrists not arms",
            "Jump with pointed toes",
            "Stay on balls of feet"
        ],
        "equipment": ["jump rope"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=6L3jqKYS1mE",
        "body_part": ["cardio", "coordination"],
        "description": [
            "Hold rope handles lightly",
            "Keep elbows close to sides",
            "Jump with pointed toes",
            "Rotate wrists for rope turn",
            "Land softly on balls of feet",
            "Maintain consistent rhythm",
            "Keep jumps small"
        ]
    },

    "PVC Overhead Squats": {
        "tips": [
            "Keep arms locked",
            "PVC slightly behind head",
            "Maintain vertical torso"
        ],
        "equipment": ["PVC pipe"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=8DNax4dN_XU",
        "body_part": ["full body", "mobility"],
        "description": [
            "Hold PVC overhead wide grip",
            "Feet shoulder width apart",
            "Keep arms locked",
            "Squat while keeping PVC stable",
            "Maintain upright torso",
            "Drive through heels",
            "Stand to full extension"
        ]
    },

    "Down Dogs": {
        "tips": [
            "Push through shoulders",
            "Keep arms straight",
            "Press heels toward ground"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=EC7RGJ975iM",
        "body_part": ["shoulders", "hamstrings", "mobility"],
        "description": [
            "Start in plank position",
            "Push hips up and back",
            "Straighten arms and legs",
            "Press chest toward thighs",
            "Push heels toward ground",
            "Hold position",
            "Keep shoulders engaged"
        ]
    },

    "Dumbbell Suitcase Carry": {
        "tips": [
            "Keep shoulders level",
            "Stand tall",
            "Engage core against lean"
        ],
        "equipment": ["dumbbells"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=raaHCkB_h0Y",
        "body_part": ["core", "grip", "obliques"],
        "description": [
            "Hold single dumbbell at side",
            "Stand tall with shoulders level",
            "Engage core against side bend",
            "Walk prescribed distance",
            "Maintain posture",
            "Control breathing",
            "Switch sides if prescribed"
        ]
    },
    "Band Pull Apart": {
        "tips": [
            "Keep arms straight throughout movement",
            "Focus on squeezing shoulder blades together",
            "Control the return, don't let band snap back"
        ],
        "equipment": ["resistance band"],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["shoulders", "back"],
        "description": [
            "Stand with arms extended in front holding band",
            "Keep arms straight and parallel to ground",
            "Pull band apart until arms are fully extended sideways",
            "Squeeze shoulder blades together at end range",
            "Control return to starting position",
            "Maintain tension throughout movement"
        ]
    },

    "Behind Neck Press": {
        "tips": [
            "Maintain active shoulders throughout movement",
            "Keep core tight for stability",
            "Ensure adequate shoulder mobility before attempting"
        ],
        "equipment": ["barbell", "plates"],
        "expertise": 3,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["shoulders", "triceps"],
        "description": [
            "Position barbell behind neck on upper traps",
            "Grip bar just outside shoulders",
            "Elbows pointed slightly forward",
            "Press bar overhead while maintaining posture",
            "Lock out arms at top",
            "Return bar under control to starting position"
        ]
    },

    "Bench Press": {
        "tips": [
            "Keep shoulders pinched and stable on bench",
            "Drive feet into floor for stability",
            "Bar path should be slightly diagonal"
        ],
        "equipment": ["barbell", "plates", "bench"],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["chest", "shoulders", "triceps"],
        "description": [
            "Lie on bench with feet flat on floor",
            "Grip bar slightly wider than shoulders",
            "Lower bar to mid-chest",
            "Keep elbows at roughly 45-degree angle",
            "Press bar up and slightly back toward head",
            "Lock out arms at top"
        ]
    },

    "Butt Kicker": {
        "tips": [
            "Stay light on toes",
            "Maintain upright posture",
            "Keep movement quick and rhythmic"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["legs", "cardio"],
        "description": [
            "Stand tall with feet hip-width apart",
            "Begin jogging in place",
            "Focus on bringing heels to glutes",
            "Keep upper body stable",
            "Arms move in running motion",
            "Maintain quick pace"
        ]
    },

    "Calf Raise": {
        "tips": [
            "Push through balls of feet",
            "Full range of motion - heel below platform",
            "Control descent phase"
        ],
        "equipment": ["box", "plates"],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["legs"],
        "description": [
            "Stand with balls of feet on edge of platform",
            "Heels hanging off edge",
            "Lower heels below platform level",
            "Drive up onto toes as high as possible",
            "Hold contracted position briefly",
            "Lower under control"
        ]
    },

    "Crab Walk": {
        "tips": [
            "Keep hips elevated throughout",
            "Coordinate hand and foot movements",
            "Maintain core engagement"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["core", "shoulders", "triceps"],
        "description": [
            "Sit with knees bent, feet flat",
            "Place hands behind body, fingers pointing toward feet",
            "Lift hips off ground",
            "Walk backward using opposite hand and foot",
            "Keep core tight and hips elevated",
            "Maintain smooth movement pattern"
        ]
    },

    "Crawl Under": {
        "tips": [
            "Keep body low to ground",
            "Move smoothly and efficiently",
            "Maintain core engagement"
        ],
        "equipment": ["bar"],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["full body"],
        "description": [
            "Start in plank position facing obstacle",
            "Keep body as flat as possible",
            "Move forward using opposite arm and leg",
            "Maintain core tension throughout",
            "Keep smooth, controlled movement",
            "Continue until cleared obstacle"
        ]
    },

    "Dumbbell Bench Press": {
        "tips": [
            "Keep dumbbells in line with middle chest",
            "Control descent phase",
            "Press dumbbells up and slightly in"
        ],
        "equipment": ["dumbbells", "bench"],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["chest", "shoulders", "triceps"],
        "description": [
            "Lie on bench holding dumbbells above chest",
            "Lower dumbbells with controlled descent",
            "Keep elbows at 45-degree angle",
            "Touch dumbbells to outside of chest",
            "Press up and slightly in",
            "Lock out arms at top"
        ]
    },

    "Dumbbell Front Rack": {
        "tips": [
            "Keep elbows high",
            "Maintain upright torso",
            "Create stable shelf with shoulders"
        ],
        "equipment": ["dumbbells"],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["shoulders", "core"],
        "description": [
            "Clean dumbbells to shoulders",
            "Create shelf with shoulders",
            "Keep elbows high and forward",
            "Maintain vertical torso",
            "Core tight for stability",
            "Hold position as prescribed"
        ]
    },

    "Dumbbell Press": {
        "tips": [
            "Start with dumbbells at shoulders",
            "Press straight up",
            "Keep core engaged"
        ],
        "equipment": ["dumbbells"],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["shoulders", "triceps"],
        "description": [
            "Hold dumbbells at shoulder height",
            "Elbows slightly forward of body",
            "Press dumbbells straight up",
            "Lock out arms overhead",
            "Lower under control",
            "Return to shoulder position"
        ]
    },

    "Dumbbell Reverse Lunge": {
        "tips": [
            "Step back far enough to keep front shin vertical",
            "Keep chest up throughout movement",
            "Control the descent"
        ],
        "equipment": ["dumbbells"],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["legs", "core"],
        "description": [
            "Hold dumbbells at sides",
            "Step backward into lunge position",
            "Lower back knee toward ground",
            "Keep front shin vertical",
            "Drive through front heel to return",
            "Alternate legs each rep"
        ]
    },

    "Dumbbell Shoulder Press": {
        "tips": [
            "Keep core tight throughout",
            "Press dumbbells straight up",
            "Full lockout at top"
        ],
        "equipment": ["dumbbells"],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["shoulders", "triceps"],
        "description": [
            "Clean dumbbells to shoulders",
            "Elbows below and slightly forward",
            "Press dumbbells overhead",
            "Achieve full lockout",
            "Lower under control",
            "Return to shoulder position"
        ]
    },

    "Front Rack Hold": {
        "tips": [
            "Keep elbows high",
            "Maintain upright posture",
            "Breathe steadily throughout hold"
        ],
        "equipment": ["barbell", "plates"],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["shoulders", "core"],
        "description": [
            "Clean barbell to front rack position",
            "Create solid rack position on shoulders",
            "Elbows high and forward",
            "Core tight for stability",
            "Maintain position for prescribed time",
            "Keep steady breathing pattern"
        ]
    },

    "Handstand Hold": {
        "tips": [
            "Stack shoulders over hands",
            "Keep core tight",
            "Practice kick-ups separately"
        ],
        "equipment": ["wall"],
        "expertise": 3,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["shoulders", "core"],
        "description": [
            "Place hands shoulder-width apart",
            "Kick up to handstand against wall",
            "Stack shoulders over hands",
            "Keep body tight and straight",
            "Maintain hollow body position",
            "Hold for prescribed time"
        ]
    },

    "High Knees": {
        "tips": [
            "Drive knees to chest height",
            "Stay on toes",
            "Maintain quick rhythm"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["legs", "cardio"],
        "description": [
            "Stand tall with feet hip-width",
            "Drive knees up alternately",
            "Aim for chest height with knees",
            "Stay on balls of feet",
            "Pump arms in running motion",
            "Maintain quick pace"
        ]
    },

    "Karaoke": {
        "tips": [
            "Stay on balls of feet",
            "Cross feet smoothly",
            "Keep hips level"
        ],
        "equipment": [],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["legs", "coordination"],
        "description": [
            "Start with feet shoulder-width apart",
            "Cross right foot behind left",
            "Step left foot to side",
            "Cross right foot in front",
            "Continue pattern laterally",
            "Maintain smooth rhythm"
        ]
    },

    "Knee To Chest": {
        "tips": [
            "Keep supporting leg straight",
            "Maintain balance",
            "Pull knee fully to chest"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["legs", "hip flexors"],
        "description": [
            "Stand tall on one leg",
            "Lift opposite knee toward chest",
            "Grasp knee with both hands",
            "Pull knee as close to chest as possible",
            "Hold position as prescribed",
            "Alternate legs"
        ]
    },

    "Med Ball Squats": {
        "tips": [
            "Hold ball at chest height",
            "Keep chest up throughout",
            "Drive through heels"
        ],
        "equipment": ["medicine ball"],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["legs", "core"],
        "description": [
            "Hold medicine ball at chest height",
            "Feet shoulder-width apart",
            "Break at hips and knees",
            "Lower until hips below parallel",
            "Drive through heels to stand",
            "Maintain upright torso"
        ]
    },

    "Prisoner Squat": {
        "tips": [
            "Keep hands behind head light",
            "Chest up throughout movement",
            "Push knees out over toes"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["legs"],
        "description": [
            "Stand with hands behind head",
            "Feet shoulder-width apart",
            "Break at hips and knees",
            "Keep chest up and core tight",
            "Lower until hips below parallel",
            "Stand to full extension"
        ]
    },

    "Reverse Lunge": {
        "tips": [
            "Step back far enough for vertical shin",
            "Keep torso upright",
            "Drive through front heel"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["legs"],
        "description": [
            "Stand with feet hip-width apart",
            "Step one leg back",
            "Lower back knee toward ground",
            "Keep front shin vertical",
            "Push through front heel to return",
            "Alternate legs each rep"
        ]
    },

    "Shoulder Press": {
        "tips": [
            "Stack bar over midline",
            "Keep core tight",
            "Full lockout overhead"
        ],
        "equipment": ["barbell", "plates"],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["shoulders", "triceps"],
        "description": [
            "Start with bar in front rack",
            "Grip just outside shoulders",
            "Press bar straight overhead",
            "Keep core tight throughout",
            "Achieve full lockout",
            "Return to rack position"
        ]
    },

    "Shoulder To Overhead": {
        "tips": [
            "Choose press, push press, or jerk",
            "Keep bar close to face",
            "Finish with active shoulders"
        ],
        "equipment": ["barbell", "plates"],
        "expertise": 3,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["shoulders", "legs"],
        "description": [
            "Start with bar in front rack",
            "Choose movement style",
            "Drive bar overhead",
            "Achieve full lockout",
            "Active shoulders at top",
            "Return to rack position"
        ]
    },

    "Single Dumbbell Press": {
        "tips": [
            "Keep core tight to prevent leaning",
            "Stack dumbbell over shoulder",
            "Control the descent"
        ],
        "equipment": ["dumbbell"],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["shoulders", "core"],
        "description": [
            "Clean dumbbell to shoulder",
            "Keep core engaged",
            "Press dumbbell straight up",
            "Achieve full lockout",
            "Lower under control",
            "Maintain midline stability"
        ]
    },

    "Single Leg Toe Touch": {
        "tips": [
            "Keep standing leg straight",
            "Hinge at hips",
            "Maintain balance throughout"
        ],
        "equipment": [],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["hamstrings", "balance"],
        "description": [
            "Stand on one leg",
            "Hinge at hip keeping back straight",
            "Reach for toe with opposite hand",
            "Keep standing leg straight",
            "Return to standing",
            "Maintain balance throughout"
        ]
    },
    "Spiderman Lunge": {
        "tips": [
            "Keep back leg straight",
            "Drop hips low into stretch",
            "Maintain control throughout movement"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["legs", "hips"],
        "description": [
            "Start in push-up position",
            "Step one foot forward outside same-side hand",
            "Lower hips into deep stretch",
            "Keep back leg straight",
            "Return foot to starting position",
            "Alternate sides"
        ]
    },

    "Spiderman Twist": {
        "tips": [
            "Keep core engaged throughout",
            "Control the rotation",
            "Stay low in lunge position"
        ],
        "equipment": [],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["core", "hips"],
        "description": [
            "Start in Spiderman lunge position",
            "Front foot outside same-side hand",
            "Lift inside arm toward ceiling",
            "Rotate torso upward",
            "Follow hand with eyes",
            "Return to starting position"
        ]
    },

    "Squat Toss": {
        "tips": [
            "Use hips to generate power",
            "Keep ball close to body",
            "Control the catch"
        ],
        "equipment": ["medicine ball"],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["legs", "core"],
        "description": [
            "Hold medicine ball at chest",
            "Perform full squat",
            "Drive explosively through hips",
            "Toss ball upward",
            "Catch ball in quarter squat",
            "Immediately begin next rep"
        ]
    },

    "Toe Touch": {
        "tips": [
            "Keep legs straight",
            "Bend from hips",
            "Reach for toes, not just down"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["hamstrings"],
        "description": [
            "Stand with feet together",
            "Keep legs straight",
            "Bend forward at hips",
            "Reach for toes",
            "Hold stretch position",
            "Return to standing"
        ]
    },

    "Twist": {
        "tips": [
            "Keep hips stable",
            "Rotate from thoracic spine",
            "Maintain upright posture"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["core"],
        "description": [
            "Stand with feet shoulder-width apart",
            "Arms extended at shoulder height",
            "Keep hips facing forward",
            "Rotate torso side to side",
            "Maintain controlled movement",
            "Keep core engaged throughout"
        ]
    },
    "Plank Reach Through": {
        "tips": [
            "Keep hips level",
            "Reach arm fully through",
            "Control rotation"
        ],
        "equipment": [],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=njDJ2xC0_HY",
        "body_part": ["core", "shoulders", "rotation"],
        "description": [
            "Start in plank position",
            "Lift one hand off ground",
            "Reach under body",
            "Rotate torso slightly",
            "Return hand to start",
            "Maintain hip position",
            "Alternate sides"
        ]
    },

    "Knee Push-ups": {
        "tips": [
            "Keep body straight from knees",
            "Full range of motion",
            "Control movement"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=jWxvty2KROs",
        "body_part": ["chest", "shoulders", "triceps"],
        "description": [
            "Start on knees and hands",
            "Keep body straight from knees up",
            "Lower chest to ground",
            "Keep elbows at 45 degrees",
            "Push back to start",
            "Maintain core tension",
            "Control movement speed"
        ]
    },

    "PVC Good Mornings": {
        "tips": [
            "PVC across upper back",
            "Hinge at hips",
            "Keep back straight"
        ],
        "equipment": ["PVC pipe"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=8aYbYT5qDZM",
        "body_part": ["hamstrings", "back"],
        "description": [
            "Place PVC across upper back",
            "Feet shoulder width apart",
            "Push hips back to hinge",
            "Keep back straight",
            "Feel hamstring stretch",
            "Drive hips forward",
            "Return to standing"
        ]
    },

    "Spiderman Reaches": {
        "tips": [
            "Step foot outside hand",
            "Open hip fully",
            "Keep back leg straight"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=LNb4T_xB4Co",
        "body_part": ["hips", "mobility"],
        "description": [
            "Start in push-up position",
            "Step foot outside same hand",
            "Drop hip toward ground",
            "Reach inside arm up",
            "Rotate torso upward",
            "Return to start",
            "Alternate sides"
        ]
    },

    "Back Rack Lunge": {
        "tips": [
            "Keep torso vertical",
            "Maintain tight back rack position",
            "Control knee tracking"
        ],
        "equipment": ["barbell", "plates"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=f3WLs_HutLw",
        "body_part": ["legs", "core"],
        "description": [
            "Position barbell on upper back",
            "Step forward into lunge",
            "Keep torso upright",
            "Lower back knee toward ground",
            "Drive through front heel",
            "Return to starting position",
            "Alternate legs each rep"
        ]
    },

    "Dumbbell Power Clean": {
        "tips": [
            "Keep dumbbells close to body",
            "Use hip drive for power",
            "Receive in athletic stance"
        ],
        "equipment": ["dumbbells"],
        "expertise": 3,
        "demo_url": "https://www.youtube.com/watch?v=2qIVRgE5yRE",
        "body_part": ["full body", "power"],
        "description": [
            "Start with dumbbells at sides",
            "Hinge at hips",
            "Drive explosively through hips",
            "Pull dumbbells to shoulders",
            "Receive in quarter squat",
            "Stand to full extension",
            "Lower dumbbells to starting position"
        ]
    },

    "Alt Samson Lunges": {
        "tips": [
            "Reach arms overhead",
            "Push hip forward",
            "Keep front knee stable"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=U1zS6RYh_BY",
        "body_part": ["hips", "mobility"],
        "description": [
            "Start in lunge position",
            "Reach arms overhead",
            "Push front hip forward",
            "Feel stretch in back hip",
            "Return to start",
            "Switch legs",
            "Maintain balance throughout"
        ]
    },

    "Plate Hold": {
        "tips": [
            "Keep shoulders packed",
            "Maintain steady position",
            "Control breathing"
        ],
        "equipment": ["weight plate"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=6l2Iu_jV6Ho",
        "body_part": ["shoulders", "core"],
        "description": [
            "Hold plate at shoulder height",
            "Keep arms straight",
            "Engage core",
            "Pack shoulders down",
            "Hold for prescribed time",
            "Maintain steady position",
            "Focus on breathing"
        ]
    },

    "Kettlebell Presses": {
        "tips": [
            "Clean bell to rack first",
            "Press straight up",
            "Lock out arm"
        ],
        "equipment": ["kettlebell"],
        "expertise": 2,
        "demo_url": "https://www.youtube.com/watch?v=0WW4kx9jV94",
        "body_part": ["shoulders", "core"],
        "description": [
            "Clean kettlebell to rack position",
            "Keep elbow tight to body",
            "Press kettlebell overhead",
            "Lock out arm completely",
            "Return to rack position",
            "Control descent",
            "Maintain core stability"
        ]
    },

    "Arm Circles": {
        "tips": [
            "Keep shoulders down",
            "Make consistent circles",
            "Increase size gradually"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=L_qEXP0U_pQ",
        "body_part": ["shoulders", "mobility"],
        "description": [
            "Stand with arms extended",
            "Make small forward circles",
            "Gradually increase circle size",
            "Reverse direction",
            "Keep shoulders down",
            "Maintain controlled movement",
            "Continue for prescribed time"
        ]
    },

    "Side Pass": {
        "tips": [
            "Rotate from core",
            "Step into throw",
            "Keep chest up"
        ],
        "equipment": ["medicine ball", "wall"],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=VG2Ays7yg_k",
        "body_part": ["core", "power"],
        "description": [
            "Stand sideways to partner/wall",
            "Hold ball at chest",
            "Rotate away",
            "Step and throw",
            "Catch return pass",
            "Control rotation",
            "Maintain athletic position"
        ]
    },

    "Elbow to Instep": {
        "tips": [
            "Keep back leg straight",
            "Get elbow to ground",
            "Open hip fully"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "https://www.youtube.com/watch?v=LNb4T_xB4Co",
        "body_part": ["hips", "mobility"],
        "description": [
            "Start in push-up position",
            "Step foot forward outside hand",
            "Drop elbow to instep",
            "Keep back leg straight",
            "Hold stretch position",
            "Return to start",
            "Alternate sides"
        ]
    },

    "Movement Drills": {
        "tips": [
            "Focus on form",
            "Move with control",
            "Build intensity gradually"
        ],
        "equipment": [],
        "expertise": 1,
        "body_part": ["full body", "mobility"],
        "description": [
            "Perform prescribed movements",
            "Start at moderate pace",
            "Focus on quality",
            "Increase speed as appropriate",
            "Maintain good form",
            "Follow specified distances",
            "Complete all variations"
        ]
    },

    "Jog": {
        "tips": [
            "Keep easy sustainable pace",
            "Focus on form over speed",
            "Maintain relaxed breathing"
        ],
        "equipment": [],
        "expertise": 1,
        "body_part": ["legs", "cardio"],
        "description": [
            "Start at easy pace",
            "Maintain conversation pace",
            "Keep relaxed form",
            "Focus on breathing",
            "Complete prescribed distance",
            "Stay consistent",
            "Cool down as needed"
        ]
    },

    "Jump Rope": {
        "tips": [
            "Stay on balls of feet",
            "Keep elbows close",
            "Use wrist rotation"
        ],
        "equipment": ["jump rope"],
        "expertise": 2,
        "body_part": ["cardio", "coordination"],
        "description": [
            "Hold rope handles lightly",
            "Stay on balls of feet",
            "Keep elbows close to sides",
            "Turn rope with wrists",
            "Jump with small bounces",
            "Maintain rhythm",
            "Complete prescribed time/reps"
        ]
    },

    "Side Tosses": {
        "tips": [
            "Rotate from core",
            "Keep arms extended",
            "Control catch position"
        ],
        "equipment": ["medicine ball", "wall"],
        "expertise": 2,
        "body_part": ["core", "power"],
        "description": [
            "Stand sideways to wall",
            "Hold med ball at hip",
            "Rotate away from wall",
            "Throw using hip rotation",
            "Catch with control",
            "Reset position",
            "Maintain athletic stance"
        ]
    },

    "Rest": {
        "tips": [
            "Keep moving if needed",
            "Control breathing",
            "Prepare for next movement"
        ],
        "equipment": [],
        "expertise": 1,
        "body_part": ["recovery"],
        "description": [
            "Stop prescribed movement",
            "Control breathing",
            "Shake out muscles if needed",
            "Stay mentally focused",
            "Watch clock/timer",
            "Prepare for next movement",
            "Resume at appropriate time"
        ]
    },

    "Counterbalance Squats": {
        "tips": [
            "Hold weight at chest",
            "Keep torso upright",
            "Push knees out"
        ],
        "equipment": ["weight plate", "dumbbell"],
        "expertise": 1,
        "body_part": ["legs", "core"],
        "description": [
            "Hold weight at chest level",
            "Feet shoulder width apart",
            "Break at hips and knees",
            "Keep torso upright",
            "Use weight as counterbalance",
            "Return to standing",
            "Maintain control throughout"
        ]
    },

    "DB Clean and Jerk": {
        "tips": [
            "Keep dumbbells close",
            "Drive through legs",
            "Lock out overhead"
        ],
        "equipment": ["dumbbells"],
        "expertise": 3,
        "body_part": ["full body"],
        "description": [
            "Start with DBs at sides",
            "Clean to shoulders",
            "Stand fully",
            "Dip slightly",
            "Drive overhead",
            "Lock out arms",
            "Return to start position"
        ]
    },

    "Pull-up": {
        "tips": [
            "Start from dead hang",
            "Pull chin over bar",
            "Control descent"
        ],
        "equipment": ["pull-up bar"],
        "expertise": 2,
        "body_part": ["back", "biceps"],
        "description": [
            "Grip bar outside shoulders",
            "Start from dead hang",
            "Pull chin over bar",
            "Keep core tight",
            "Lower with control",
            "Return to dead hang",
            "Repeat for prescribed reps"
        ]
    },
    "Back Rack Position": {
        "tips": [
            "Keep elbows high and forward",
            "Create solid shelf with shoulders",
            "Maintain upright torso"
        ],
        "equipment": ["barbell"],
        "expertise": 2,
        "demo_url": "",
        "body_part": ["shoulders", "core", "upper back"],
        "description": [
            "Position barbell across front deltoids",
            "Elbows pointed forward and up",
            "Create stable shelf with shoulders",
            "Keep torso upright",
            "Maintain neutral wrist position",
            "Core engaged throughout",
            "Practice with empty barbell first"
        ]
    },

    "Chest Passes": {
        "tips": [
            "Step into throw",
            "Follow through with hands",
            "Keep ball at chest level"
        ],
        "equipment": ["medicine ball", "wall"],
        "expertise": 1,
        "demo_url": "",
        "body_part": ["chest", "shoulders", "core"],
        "description": [
            "Hold ball at chest height",
            "Elbows out to sides",
            "Step forward as you push",
            "Extend arms fully on release",
            "Follow through with hands",
            "Catch ball with soft hands",
            "Reset position for next rep"
        ]
    },

    "Down And Back Movements": {
        "tips": [
            "Maintain consistent pace",
            "Control breathing pattern",
            "Focus on form over speed"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "",
        "body_part": ["full body", "cardio"],
        "description": [
            "Mark set distance for drill",
            "Perform prescribed movement down",
            "Turn around controlled",
            "Return using same movement",
            "Maintain form throughout",
            "Complete specified rounds",
            "Scale distance as needed"
        ]
    },

    "Elbow Raises": {
        "tips": [
            "Keep shoulder blades pulled back",
            "Control movement speed",
            "Maintain upright posture"
        ],
        "equipment": ["barbell"],
        "expertise": 1,
        "demo_url": "",
        "body_part": ["shoulders", "upper back"],
        "description": [
            "Start with bar in back rack",
            "Drive elbows up toward ceiling",
            "Keep shoulder blades retracted",
            "Control downward movement",
            "Maintain upright torso",
            "Perform prescribed reps",
            "Focus on full range of motion"
        ]
    },

    "Granny Tosses": {
        "tips": [
            "Use leg drive for power",
            "Keep ball close to body",
            "Follow through overhead"
        ],
        "equipment": ["medicine ball", "wall"],
        "expertise": 1,
        "demo_url": "",
        "body_part": ["legs", "shoulders", "core"],
        "description": [
            "Hold ball between legs",
            "Squat down with ball",
            "Drive through legs",
            "Swing ball overhead",
            "Release at full extension",
            "Follow through with arms",
            "Catch and repeat fluid motion"
        ]
    },

    "Handstand Walk": {
        "tips": [
            "Keep arms locked",
            "Look between hands",
            "Take small controlled steps"
        ],
        "equipment": [],
        "expertise": 4,
        "demo_url": "",
        "body_part": ["shoulders", "core", "balance"],
        "description": [
            "Kick up to handstand position",
            "Lock arms fully",
            "Look between hands",
            "Keep core tight",
            "Take small steps forward",
            "Maintain balance through shoulders",
            "Practice against wall first"
        ]
    },

    "Hollow Hold": {
        "tips": [
            "Press lower back down",
            "Point toes",
            "Squeeze everything"
        ],
        "equipment": [],
        "expertise": 2,
        "demo_url": "",
        "body_part": ["core", "hip flexors"],
        "description": [
            "Lie on back",
            "Press lower back to ground",
            "Lift shoulders off ground",
            "Raise legs with straight knees",
            "Point toes",
            "Hold position",
            "Maintain tension throughout"
        ]
    },

    "Jumping Jacks": {
        "tips": [
            "Coordinate arms and legs",
            "Land softly",
            "Keep rhythm consistent"
        ],
        "equipment": [],
        "expertise": 1,
        "demo_url": "",
        "body_part": ["full body", "cardio"],
        "description": [
            "Start with feet together",
            "Arms at sides",
            "Jump feet out wide",
            "Simultaneously raise arms overhead",
            "Jump feet back together",
            "Lower arms to sides",
            "Maintain steady rhythm"
        ]
    },
    "Medicine Ball Pass": {
        "tips": [
            "Use legs for power",
            "Keep core tight",
            "Communicate with partner"
        ],
        "equipment": ["medicine ball"],
        "expertise": 1,
        "demo_url": "",
        "body_part": ["full body", "coordination"],
        "description": [
            "Face partner or wall",
            "Hold ball at chest",
            "Slight knee bend",
            "Drive through legs",
            "Push ball forcefully",
            "Follow through with hands",
            "Catch with soft hands"
        ]
    },

    "PVC Movements": {
        "tips": [
            "Keep arms straight",
            "Control movement speed",
            "Focus on mobility"
        ],
        "equipment": ["PVC pipe"],
        "expertise": 1,
        "demo_url": "",
        "body_part": ["shoulders", "mobility"],
        "description": [
            "Hold PVC with wide grip",
            "Keep arms straight",
            "Perform prescribed movement",
            "Maintain control throughout",
            "Focus on full range",
            "Scale grip width as needed",
            "Progress movement speed gradually"
        ]
    },

    "PVC Overhead Lunges": {
        "tips": [
            "Keep PVC behind head plane",
            "Maintain vertical torso",
            "Control knee tracking"
        ],
        "equipment": ["PVC pipe"],
        "expertise": 2,
        "demo_url": "",
        "body_part": ["legs", "shoulders", "core"],
        "description": [
            "Hold PVC overhead",
            "Arms fully locked",
            "Step forward into lunge",
            "Keep torso vertical",
            "Lower back knee toward ground",
            "Drive through front heel",
            "Maintain overhead position"
        ]
    },

    "PVC Switch": {
        "tips": [
            "Maintain grip width",
            "Keep arms straight",
            "Control movement path"
        ],
        "equipment": ["PVC pipe"],
        "expertise": 1,
        "demo_url": "",
        "body_part": ["shoulders", "mobility"],
        "description": [
            "Hold PVC with wide grip",
            "Start in front of body",
            "Pass pipe over head",
            "Bring to back position",
            "Return to front",
            "Maintain straight arms",
            "Control movement speed"
        ]
    },

    "Single Leg Squat": {
        "tips": [
            "Keep weight in heel",
            "Maintain balance",
            "Control descent"
        ],
        "equipment": [],
        "expertise": 3,
        "demo_url": "",
        "body_part": ["legs", "balance", "core"],
        "description": [
            "Stand on one leg",
            "Other leg straight out front",
            "Squat on support leg",
            "Keep torso upright",
            "Lower under control",
            "Drive through heel",
            "Stand to full extension"
        ]
    },

    "Sit Ups": {
        "tips": [
            "Anchor feet securely",
            "Keep core engaged",
            "Control both up and down"
        ],
        "equipment": ["mat"],
        "expertise": 1,
        "demo_url": "",
        "body_part": ["core", "hip flexors"],
        "description": [
            "Lie on back",
            "Bend knees, feet flat",
            "Hands behind head",
            "Lift shoulders off ground",
            "Curl up to full sit-up",
            "Lower under control",
            "Maintain consistent pace"
        ]
    },

    "Step Ups": {
        "tips": [
            "Drive through heel",
            "Stand fully at top",
            "Control step down"
        ],
        "equipment": ["box"],
        "expertise": 1,
        "demo_url": "",
        "body_part": ["legs", "balance"],
        "description": [
            "Stand facing box",
            "Place one foot fully on box",
            "Drive through heel",
            "Stand to full extension",
            "Control step down",
            "Alternate legs",
            "Maintain upright posture"
        ]
    },

    "Strict Press": {
        "tips": [
            "Keep core tight",
            "Press straight up",
            "Lock out arms"
        ],
        "equipment": ["barbell", "plates"],
        "expertise": 2,
        "demo_url": "",
        "body_part": ["shoulders", "triceps", "core"],
        "description": [
            "Start in front rack position",
            "Elbows slightly forward",
            "Brace core tight",
            "Press bar straight up",
            "Push head through at top",
            "Lock out arms fully",
            "Return to rack position"
        ]
    },

    "Underhand Toss": {
        "tips": [
            "Use leg drive",
            "Keep ball close",
            "Follow through up"
        ],
        "equipment": ["medicine ball"],
        "expertise": 1,
        "demo_url": "",
        "body_part": ["legs", "shoulders"],
        "description": [
            "Hold ball at waist level",
            "Slight knee bend",
            "Drive through legs",
            "Swing arms upward",
            "Release ball at chest height",
            "Follow through overhead",
            "Catch and reset position"
        ]
    },
    "Kip Swing": {
        "tips": [
            "Generate power from shoulders and lats",
            "Keep core tight throughout movement",
            "Maintain hollow and arch positions"
        ],
        "equipment": ["pull-up bar"],
        "expertise": 2,
        "demo_url": "",
        "body_part": ["shoulders", "back", "core"],
        "description": [
            "Start in hang position with shoulders active",
            "Create hollow position with ribs down",
            "Push away from bar into arch position",
            "Pull back to hollow maintaining tension",
            "Build rhythm and power gradually",
            "Keep shoulders engaged throughout",
            "Control swing amplitude"
        ]
    },

    "PVC Work": {
        "tips": [
            "Keep arms straight during movements",
            "Focus on full range of motion",
            "Move slowly and controlled"
        ],
        "equipment": ["PVC pipe"],
        "expertise": 1,
        "demo_url": "",
        "body_part": ["shoulders", "mobility", "core"],
        "description": [
            "Hold PVC pipe with wide grip",
            "Start with basic pass-throughs",
            "Progress to overhead positions",
            "Practice front rack position",
            "Perform prescribed mobility drills",
            "Maintain straight arms throughout",
            "Focus on position and control"
        ]
    },
    "Leg Press": {
        "tips": [
            "Keep feet shoulder width apart on platform",
            "Control eccentric phase with no bouncing",
            "Drive through heels and maintain full foot contact"
        ],
        "equipment": ["leg press machine"],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["legs"],
        "description": [
            "Adjust seat position so knees don't pass 90 degrees at bottom",
            "Place feet shoulder width on platform, toes slightly out",
            "Unrack weight by straightening legs",
            "Lower weight under control until legs reach 90 degrees",
            "Drive through heels to press weight up",
            "Stop just short of lockout to maintain tension",
            "Maintain neutral spine throughout movement"
        ]
    },
    "Roll Pass": {
        "tips": [
            "Keep core tight throughout movement",
            "Roll smoothly without losing tension",
            "Pass medicine ball with control and accuracy"
        ],
        "equipment": ["med ball"],
        "expertise": 1,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["shoulders"],
        "description": [
            "Partners lie on back about 6 feet apart",
            "First partner holds medicine ball at chest",
            "Roll to one side while keeping core engaged",
            "Pass ball to partner as you roll",
            "Return to center as partner receives ball",
            "Partner repeats movement in opposite direction",
            "Maintain continuous, controlled movement pattern"
        ]
    },
    "Weighted Ab Mat Sit Up": {
        "tips": [
            "Keep weight plate close to chest throughout",
            "Use hip flexors to initiate movement",
            "Control descent to protect lower back"
        ],
        "equipment": ["mat", "plate"],
        "expertise": 2,
        "demo_url": "",
        "crossfit_url": "",
        "body_part": ["abs"],
        "description": [
            "Position AbMat under lower back",
            "Hold weight plate at chest level",
            "Feet anchored, arms extended holding plate",
            "Engage core and lift torso up",
            "Touch plate to ground behind head",
            "Control return to starting position",
            "Keep weight close to body throughout movement"
        ]
    }
}


TRAININGS = [
    {
        "exercises_used": ["Front Squat", "Bar Muscle Up", "Kettlebell Swing"],
        "training_program": {
            "EMOM 18": {
                1: {"Front Squat": {"reps": 3, "weight": "@80%"}},
                2: {"Bar Muscle Up": {"reps": 2, "notes": "Any style"}},
                3: {"Kettlebell Swing": {"reps": 15, "weight": "32/24kg", "notes": "Russian style"}}
            }
        },
        "training_type": "metcon",
        "training_time": 18
    },

    {
        "exercises_used": ["Power Snatch", "Box Jump Over", "GHD Sit-Up"],
        "training_program": {
            "AMRAP 12": {
                "round_target": {
                    "Power Snatch": {"reps": 7, "weight": "60/40kg"},
                    "Box Jump Over": {"reps": 12, "height": "24/20inch"},
                    "GHD Sit-Up": {"reps": 15}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 12
    },

    {
        "exercises_used": ["Thruster", "Pull-up", "Running"],
        "training_program": {
            "For Time": {
                "round_target": {
                    "Thruster": {"reps": 21 - 15 - 9, "weight": "42.5/30kg"},
                    "Pull-up": {"reps": 21 - 15 - 9},
                    "Running": {"distance": "400m between rounds"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 25
    },

    {
        "exercises_used": ["Clean", "Ring Dip", "Devils Press"],
        "training_program": {
            "4 Rounds": {
                "round_target": {
                    "Clean": {"reps": 5, "weight": "@75%"},
                    "Ring Dip": {"reps": 10, "notes": "Strict"},
                    "Devils Press": {"reps": 8, "weight": "22.5/15kg"}
                },
                "rest": "1.30 min between rounds"
            }
        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "exercises_used": ["Overhead Squat", "Chest to Bar Pull-up", "Double Under"],
        "training_program": {
            "EMOM 15": {
                1: {"Overhead Squat": {"reps": 3, "weight": "@70%"}},
                2: {"Chest to Bar Pull-up": {"reps": 6}},
                3: {"Double Under": {"reps": 30}}
            }
        },
        "training_type": "metcon",
        "training_time": 15
    },

    {
        "exercises_used": ["Push Press", "Toes to Bar", "Assault Bike"],
        "training_program": {
            "5 Rounds": {
                "round_target": {
                    "Push Press": {"reps": 12, "weight": "@65%"},
                    "Toes to Bar": {"reps": 15},
                    "Assault Bike": {"calories": 12}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 25
    },

    {
        "exercises_used": ["Deadlift", "Handstand Walk", "Row"],
        "training_program": {
            "Every 4 min x 5": {
                "round_target": {
                    "Deadlift": {"reps": 8, "weight": "@70%"},
                    "Handstand Walk": {"distance": "15m"},
                    "Row": {"calories": 15}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "exercises_used": ["Power Clean", "Burpee Over Bar", "Wall Ball"],
        "training_program": {
            "AMRAP 16": {
                "round_target": {
                    "Power Clean": {"reps": 5, "weight": "60/40kg"},
                    "Burpee Over Bar": {"reps": 5},
                    "Wall Ball": {"reps": 15, "weight": "20/14lbs"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 16
    },

    {
        "exercises_used": ["Back Squat", "Strict Press", "Pull-up"],
        "training_program": {
            "Strength": {
                1: {"Back Squat": {"sets": 5, "reps": 5, "weight": "@75-80%"}},
                2: {"Strict Press": {"sets": 5, "reps": 5, "weight": "@70-75%"}},
                3: {"Pull-up": {"sets": 5, "reps": "Max Strict"}}
            }
        },
        "training_type": "strength",
        "training_time": 45
    },

    {
        "exercises_used": ["Hang Power Snatch", "Box Step-up", "Hollow Rock"],
        "training_program": {
            "3 Rounds": {
                "round_target": {
                    "Hang Power Snatch": {"reps": 7, "weight": "43/30kg"},
                    "Box Step-up": {"reps": "15/leg", "height": "24/20inch"},
                    "Hollow Rock": {"reps": 20}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "exercises_used": ["Turkish Get-Up", "Rope Climb", "Running"],
        "training_program": {
            "EMOM 24": {
                1: {"Turkish Get-Up": {"reps": "1/side", "weight": "24/16kg"}},
                2: {"Rope Climb": {"reps": 1}},
                3: {"Running": {"distance": "200m"}}
            }
        },
        "training_type": "metcon",
        "training_time": 24
    },

    {
        "exercises_used": ["Sumo Deadlift High Pull", "Air Squat", "Push-up"],
        "training_program": {
            "21-15-9": {
                "round_target": {
                    "Sumo Deadlift High Pull": {"reps": "21-15-9", "weight": "35/25kg"},
                    "Air Squat": {"reps": "21-15-9"},
                    "Push-up": {"reps": "21-15-9"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 15
    },

    {
        "exercises_used": ["Clean and Jerk", "Ring Muscle Up", "Double Under"],
        "training_program": {
            "Every 5 min x 6": {
                "round_target": {
                    "Clean and Jerk": {"reps": 3, "weight": "@80%"},
                    "Ring Muscle Up": {"reps": 3},
                    "Double Under": {"reps": 50}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 30
    },

    {
        "exercises_used": ["Front Rack Lunge", "Pistol", "Rowing"],
        "training_program": {
            "AMRAP 20": {
                "round_target": {
                    "Front Rack Lunge": {"reps": "10/leg", "weight": "22.5/15kg DB"},
                    "Pistol": {"reps": "5/leg"},
                    "Rowing": {"calories": 15}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "exercises_used": ["Push Jerk", "Farmers Carry", "Burpee"],
        "training_program": {
            "4 Rounds": {
                "round_target": {
                    "Push Jerk": {"reps": 10, "weight": "@65%"},
                    "Farmers Carry": {"distance": "30m", "weight": "32/24kg KB"},
                    "Burpee": {"reps": 12}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "exercises_used": ["Dumbbell Snatch", "Box Jump", "Sit-up"],
        "training_program": {
            "EMOM 12": {
                1: {"Dumbbell Snatch": {"reps": "6/arm", "weight": "22.5/15kg"}},
                2: {"Box Jump": {"reps": 8, "height": "24/20inch"}},
                3: {"Sit-up": {"reps": 12}}
            }
        },
        "training_type": "metcon",
        "training_time": 12
    },

    {
        "exercises_used": ["Overhead Walking Lunge", "Handstand Push-up", "KBS"],
        "training_program": {
            "For Time": {
                "round_target": {
                    "Overhead Walking Lunge": {"distance": "30m", "weight": "22.5/15kg DB"},
                    "Handstand Push-up": {"reps": 12},
                    "KBS": {"reps": 20, "weight": "32/24kg"}
                },
                "rounds": 3
            }
        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "exercises_used": ["Power Clean", "Thruster", "Bar Facing Burpee"],
        "training_program": {
            "Death by": {
                "round_target": {
                    "Power Clean": {"reps": "1 more each min", "weight": "60/40kg"},
                    "Thruster": {"reps": "1 more each min", "weight": "60/40kg"},
                    "Bar Facing Burpee": {"reps": "1 more each min"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": "until failure"
    },

    {
        "exercises_used": ["Ring Dip", "L-Sit Hold", "Running"],
        "training_program": {
            "5 Rounds": {
                "round_target": {
                    "Ring Dip": {"reps": 10, "notes": "Strict"},
                    "L-Sit Hold": {"time": "20 seconds"},
                    "Running": {"distance": "200m"}
                },
                "rest": "1 min between rounds"
            }
        },
        "training_type": "metcon",
        "training_time": 25
    },

    {
        "exercises_used": ["Deficit Handstand Push-up", "Toes to Bar", "Double Under"],
        "training_program": {
            "AMRAP 15": {
                "round_target": {
                    "Deficit Handstand Push-up": {"reps": 5, "deficit": "1 inch"},
                    "Toes to Bar": {"reps": 10},
                    "Double Under": {"reps": 30}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 15
    },

    {
        "exercises_used": ["Clean", "Front Squat", "Jerk"],
        "training_program": {
            "Every 2 min x 10": {
                "round_target": {
                    "Clean": {"reps": 1, "weight": "@80%"},
                    "Front Squat": {"reps": 2, "weight": "Same"},
                    "Jerk": {"reps": 1, "weight": "Same"}
                }
            }
        },
        "training_type": "strength",
        "training_time": 20
    },

    {
        "exercises_used": ["Devil Press", "Rope Climb", "Wall Ball"],
        "training_program": {
            "3 Rounds": {
                "round_target": {
                    "Devil Press": {"reps": 12, "weight": "22.5/15kg DB"},
                    "Rope Climb": {"reps": 3},
                    "Wall Ball": {"reps": 20, "weight": "20/14lbs"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "exercises_used": ["Back Squat", "Strict Pull-up", "GHD Sit-up"],
        "training_program": {
            "Every 3 min x 5": {
                "round_target": {
                    "Back Squat": {"reps": 5, "weight": "@75%"},
                    "Strict Pull-up": {"reps": 7},
                    "GHD Sit-up": {"reps": 12}
                }
            }
        },
        "training_type": "strength",
        "training_time": 15
    },

    {
        "exercises_used": ["Power Snatch", "Assault Bike", "Ring Row"],
        "training_program": {
            "EMOM 20": {
                1: {"Power Snatch": {"reps": 3, "weight": "@70%"}},
                2: {"Assault Bike": {"calories": 10}},
                3: {"Ring Row": {"reps": 12}}
            },
            "rest": "1 min between rounds"

        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "exercises_used": ["Deadlift", "Box Step-up", "Hollow Rock"],
        "training_program": {
            "10-9-8-7-6-5-4-3-2-1": {
                "round_target": {
                    "Deadlift": {"reps": "descending", "weight": "100/70kg"},
                    "Box Step-up": {"reps": "descending/leg", "height": "24/20inch"},
                    "Hollow Rock": {"reps": "descending x 3"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 25
    },

    {
        "exercises_used": ["Clean and Jerk", "Chest to Bar Pull-up", "Running"],
        "training_program": {
            "Every 6 min x 5": {
                "round_target": {
                    "Clean and Jerk": {"reps": 5, "weight": "@70%"},
                    "Chest to Bar Pull-up": {"reps": 10},
                    "Running": {"distance": "400m"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 30
    },
    {
        "exercises_used": ["Muscle Up", "Power Clean", "Box Jump"],
        "training_program": {
            "Every 2 min x 10": {
                "round_target": {
                    "Muscle Up": {"reps": 2, "notes": "Any style"},
                    "Power Clean": {"reps": 3, "weight": "60/40kg"},
                    "Box Jump": {"reps": 5, "height": "30/24inch"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "exercises_used": ["Strict Press", "Rowing", "Pistol"],
        "training_program": {
            "AMRAP 15": {
                "round_target": {
                    "Strict Press": {"reps": 7, "weight": "@65%"},
                    "Rowing": {"calories": 12},
                    "Pistol": {"reps": "5/leg"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 15
    },

    {
        "exercises_used": ["Front Squat", "Strict Pull-up", "Assault Bike"],
        "training_program": {
            "5 Rounds": {
                "round_target": {
                    "Front Squat": {"reps": 5, "weight": "@80%"},
                    "Strict Pull-up": {"reps": 8},
                    "Assault Bike": {"calories": 15}
                },
                "rest": "2 min between rounds"
            }
        },
        "training_type": "strength",
        "training_time": 30
    },

    {
        "exercises_used": ["Hang Power Snatch", "Double Under", "GHD Sit-up"],
        "training_program": {
            "For Time": {
                "round_target": {
                    "Hang Power Snatch": {"reps": "30-20-10", "weight": "43/30kg"},
                    "Double Under": {"reps": "90-60-30"},
                    "GHD Sit-up": {"reps": "30-20-10"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "exercises_used": ["Clean and Jerk", "Burpee", "Ring Row"],
        "training_program": {
            "EMOM 18": {
                1: {"Clean and Jerk": {"reps": 2, "weight": "@75%"}},
                2: {"Burpee": {"reps": 8}},
                3: {"Ring Row": {"reps": 12}}
            }
        },
        "training_type": "metcon",
        "training_time": 18
    },

    {
        "exercises_used": ["Overhead Squat", "Bar Muscle Up", "Running"],
        "training_program": {
            "4 Rounds": {
                "round_target": {
                    "Overhead Squat": {"reps": 8, "weight": "@65%"},
                    "Bar Muscle Up": {"reps": 3},
                    "Running": {"distance": "400m"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 25
    },

    {
        "exercises_used": ["Back Squat", "Handstand Push-up", "Toes to Bar"],
        "training_program": {
            "Every 5 min x 5": {
                "round_target": {
                    "Back Squat": {"reps": 3, "weight": "@85%"},
                    "Handstand Push-up": {"reps": 10},
                    "Toes to Bar": {"reps": 15}
                }
            }
        },
        "training_type": "strength",
        "training_time": 25
    },

    {
        "exercises_used": ["Turkish Get-Up", "KB Swing", "Box Step-up"],
        "training_program": {
            "AMRAP 20": {
                "round_target": {
                    "Turkish Get-Up": {"reps": "2/side", "weight": "24/16kg"},
                    "KB Swing": {"reps": 20, "weight": "32/24kg"},
                    "Box Step-up": {"reps": "10/leg", "height": "24/20inch"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "exercises_used": ["Push Press", "Chest to Bar Pull-up", "Wall Ball"],
        "training_program": {
            "21-15-9": {
                "round_target": {
                    "Push Press": {"reps": "21-15-9", "weight": "52/35kg"},
                    "Chest to Bar Pull-up": {"reps": "21-15-9"},
                    "Wall Ball": {"reps": "21-15-9", "weight": "20/14lbs"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 15
    },

    {
        "exercises_used": ["Deadlift", "Ring Muscle Up", "Hollow Rock"],
        "training_program": {
            "Every 3 min x 6": {
                "round_target": {
                    "Deadlift": {"reps": 5, "weight": "@75%"},
                    "Ring Muscle Up": {"reps": 2},
                    "Hollow Rock": {"reps": 20}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 18
    },

    {
        "exercises_used": ["Power Snatch", "Burpee Over Bar", "Double Under"],
        "training_program": {
            "AMRAP 12": {
                "round_target": {
                    "Power Snatch": {"reps": 5, "weight": "43/30kg"},
                    "Burpee Over Bar": {"reps": 5},
                    "Double Under": {"reps": 40}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 12
    },

    {
        "exercises_used": ["Front Rack Lunge", "Rope Climb", "Row"],
        "training_program": {
            "3 Rounds": {
                "round_target": {
                    "Front Rack Lunge": {"reps": "15/leg", "weight": "52/35kg"},
                    "Rope Climb": {"reps": 3},
                    "Row": {"calories": 20}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 25
    },

    {
        "exercises_used": ["Clean", "Ring Dip", "Air Squat"],
        "training_program": {
            "Every 4 min x 5": {
                "round_target": {
                    "Clean": {"reps": 3, "weight": "@80%"},
                    "Ring Dip": {"reps": 10, "notes": "Strict"},
                    "Air Squat": {"reps": 20}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "exercises_used": ["Thruster", "Pull-up", "Assault Bike"],
        "training_program": {
            "Death by": {
                "round_target": {
                    "Thruster": {"reps": "2 more each min", "weight": "43/30kg"},
                    "Pull-up": {"reps": "2 more each min"},
                    "Assault Bike": {"calories": "2 more each min"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": "until failure"
    },

    {
        "exercises_used": ["Dumbbell Snatch", "Box Jump Over", "Sit-up"],
        "training_program": {
            "EMOM 15": {
                1: {"Dumbbell Snatch": {"reps": "5/arm", "weight": "22.5/15kg"}},
                2: {"Box Jump Over": {"reps": 10, "height": "24/20inch"}},
                3: {"Sit-up": {"reps": 15}}
            }
        },
        "training_type": "metcon",
        "training_time": 15
    },

    {
        "exercises_used": ["Push Jerk", "Strict Pull-up", "Running"],
        "training_program": {
            "5 Rounds": {
                "round_target": {
                    "Push Jerk": {"reps": 7, "weight": "@70%"},
                    "Strict Pull-up": {"reps": 5},
                    "Running": {"distance": "200m"}
                },
                "rest": "1 min between rounds"
            }
        },
        "training_type": "metcon",
        "training_time": 25
    },

    {
        "exercises_used": ["Back Squat", "Handstand Walk", "GHD Sit-up"],
        "training_program": {
            "Every 2 min x 12": {
                "round_target": {
                    "Back Squat": {"reps": 2, "weight": "@85%"},
                    "Handstand Walk": {"distance": "15m"},
                    "GHD Sit-up": {"reps": 10}
                }
            }
        },
        "training_type": "strength",
        "training_time": 24
    },

    {
        "exercises_used": ["Power Clean", "Ring Muscle Up", "Wall Ball"],
        "training_program": {
            "For Time": {
                "round_target": {
                    "Power Clean": {"reps": 50, "weight": "60/40kg"},
                    "Ring Muscle Up": {"reps": 30},
                    "Wall Ball": {"reps": 100, "weight": "20/14lbs"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 30
    },

    {
        "exercises_used": ["Devils Press", "Double Under", "Toes to Bar"],
        "training_program": {
            "AMRAP 18": {
                "round_target": {
                    "Devils Press": {"reps": 10, "weight": "22.5/15kg"},
                    "Double Under": {"reps": 50},
                    "Toes to Bar": {"reps": 15}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 18
    },

    {
        "exercises_used": ["Snatch", "Bar Muscle Up", "Box Jump"],
        "training_program": {
            "Every 3 min x 7": {
                "round_target": {
                    "Snatch": {"reps": 2, "weight": "@75%"},
                    "Bar Muscle Up": {"reps": 3},
                    "Box Jump": {"reps": 8, "height": "30/24inch"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 21
    },

    {
        "exercises_used": ["Front Squat", "Push-up", "Row"],
        "training_program": {
            "4 Rounds": {
                "round_target": {
                    "Front Squat": {"reps": 10, "weight": "@65%"},
                    "Push-up": {"reps": 20},
                    "Row": {"meters": 250}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "exercises_used": ["Clean and Jerk", "Pistol", "Assault Bike"],
        "training_program": {
            "EMOM 21": {
                1: {"Clean and Jerk": {"reps": 2, "weight": "@75%"}},
                2: {"Pistol": {"reps": "5/leg"}},
                3: {"Assault Bike": {"calories": 12}}
            }
        },
        "training_type": "metcon",
        "training_time": 21
    },

    {
        "exercises_used": ["Deadlift", "Deficit HSPU", "Running"],
        "training_program": {
            "5 Rounds": {
                "round_target": {
                    "Deadlift": {"reps": 6, "weight": "@75%"},
                    "Deficit HSPU": {"reps": 8, "deficit": "2 inches"},
                    "Running": {"distance": "200m"}
                },
                "rest": "90 sec between rounds"
            }
        },
        "training_type": "metcon",
        "training_time": 25
    },

    {
        "exercises_used": ["Overhead Walking Lunge", "Pull-up", "KB Swing"],
        "training_program": {
            "AMRAP 16": {
                "round_target": {
                    "Overhead Walking Lunge": {"distance": "20m", "weight": "25/15kg DB"},
                    "Pull-up": {"reps": 12},
                    "KB Swing": {"reps": 15, "weight": "32/24kg"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 16
    },

    {
        "exercises_used": ["Turkish Get-Up", "Rope Climb", "Wall Ball"],
        "training_program": {
            "Every 4 min x 6": {
                "round_target": {
                    "Turkish Get-Up": {"reps": "2/side", "weight": "24/16kg"},
                    "Rope Climb": {"reps": 2},
                    "Wall Ball": {"reps": 20, "weight": "20/14lbs"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 24
    },

    {
        "exercises_used": ["Power Clean", "GHD Sit-up", "Box Step-up"],
        "training_program": {
            "10-8-6-4-2": {
                "round_target": {
                    "Power Clean": {"reps": "descending", "weight": "70/47.5kg"},
                    "GHD Sit-up": {"reps": "descending x 3"},
                    "Box Step-up": {"reps": "descending/leg", "height": "24/20inch"}
                }
            }
        },
        "training_type": "metcon",
        "training_time": 20
    },

    {
        "warm_up": {
            "exercises_used": ["Jumping Jacks", "Inch Worms", "Samson Stretch Lunges", "Ring Rows"],
            "training_program": {
                "2 rounds": {
                    "Jumping Jacks": {"reps": 20},
                    "Inch Worms": {"reps": 5},
                    "Samson Stretch Lunges": {"reps": 10},
                    "Ring Rows": {"reps": 10, "notes": "increase difficulty each round"}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Pull-ups", "Push-ups", "Air Squats"],
            "training_program": {
                "AMRAP 20": {
                    "Pull-ups": {"reps": 5},
                    "Push-ups": {"reps": 10},
                    "Air Squats": {"reps": 15}
                }
            },
            "training_type": "metcon",
            "training_time": 20,
            "name": "CINDY"
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Plate Ground-to-Overhead", "Plate Counterbalance Squats", "Ring Rows", "Running"],
            "training_program": {
                "2 rounds": {
                    "Plate Ground-to-Overhead": {"reps": 10},
                    "Plate Counterbalance Squats": {"reps": 10},
                    "Ring Rows": {"reps": 10},
                    "Running": {"distance": ["400m", "200m"]}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Strict Pull-up", "Deadlift", "Wall Ball", "Farmers Carry"],
            "training_program": {
                "For Time": {
                    "round_target": [
                        {"Strict Pull-up": {"reps": 15}},
                        {"Deadlift": {"reps": 25, "weight": "100/70kg"}},
                        {"Wall Ball": {"reps": 50, "weight": "20/14lbs"}},
                        {"Farmers Carry": {"distance": "down stairs", "weight": "32/24kg"}},
                        {"Wall Ball": {"reps": 50, "weight": "20/14lbs"}},
                        {"Deadlift": {"reps": 25, "weight": "100/70kg"}},
                        {"Strict Pull-up": {"reps": 15}}
                    ]
                }
            },
            "training_type": "metcon",
            "training_time": 20,

        }
    },
    {
        "metcon": {
            "exercises_used": ["Assault Bike", "Devil Press"],
            "training_program": {
                "4 Rounds": {
                    "Assault Bike": {"calories": "100/80"},
                    "Devil Press": {"reps": 14, "weight": "22.5/15kg"}
                },
                "rest": "2 min between rounds"

            },
            "training_type": "metcon",
            "training_time": 33,

        }
    },

    {
        "warm_up": {
            "exercises_used": ["Running", "Spiderman Stretches", "Plank Reach Through", "Single Leg V-ups",
                               "Scap Pull-ups"],
            "training_program": {
                "2 sets": {
                    "Running": {"distance": "200m"},
                    "Alternating Spiderman Stretches": {"reps": 10},
                    "Plank Reach Through": {"reps": 10},
                    "Single Leg V-ups": {"reps": 10},
                    "Scap Pull-ups": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Toes to Bar", "Wall Walks"],
            "training_program": {
                "AMRAP 10": {
                    "Toes to Bar": {"reps": "3-6-9-12"},
                    "Wall Walks": {"reps": "1-2-3-4"}
                }
            },
            "training_type": "metcon",
            "training_time": 10
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Single Unders", "Jump Rope Variations"],
            "training_program": {
                "rounds": {
                    "Single Unders": {"reps": 30,
                                      "notes": "Jog in Place reps 20 "
                                          "Jump Front to Back reps 20 "
                                          "Jump Side to Side reps 20"
                                          "Left Leg reps 20"
                                          "Right Leg reps 20"
                                      }

                }
            },
            "training_type": "warm-up",
            "training_time": 8
        }
    },
    {
        "metcon": {
            "exercises_used": ["Deadlift", "Hang Power Clean", "Front Squat"],
            "training_program": {
                "For Time": {
                    "round_target": {
                        "Deadlift": {"reps": "7-7-5", "weight": "62.5/45kg"},
                        "Hang Power Clean": {"reps": "prescribed"},
                        "Front Squat": {"reps": "prescribed"}
                    }
                }
            },
            "training_type": "metcon",
            "training_time": 8,

        }
    },

    {
        "warm_up": {
            "exercises_used": ["PVC Movements", "Mountain Climbers", "Air Squats"],
            "training_program": {
                "rounds": {
                    "PVC Good Mornings": {"reps": 10},
                    "PVC Overhead Lunges": {"reps": 10},
                    "PVC Pass Throughs": {"reps": 10},
                    "Mountain Climbers": {"reps": 20},
                    "Air Squats": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Power Clean", "Bar Muscle Up", "Running"],
            "training_program": {
                "Every 2 min x 10": {
                    "round_target": {
                        "Power Clean": {"reps": 3, "weight": "60/40kg"},
                        "Bar Muscle Up": {"reps": 2},
                        "Box Jump": {"reps": 5, "height": "30/24inch"}
                    }
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Back Rack Position", "Elbow Raises"],
            "training_program": {
                "rounds": {
                    "Back Rack Elbow Raise Right": {"reps": 20},
                    "Back Rack Elbow Raise Left": {"reps": 20},
                    "Back Rack Alternating Elbow Raise": {"reps": 20},
                    "Back Rack Both Elbows": {"reps": 20}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["DB Snatch", "Box Step-up", "Double Under"],
            "training_program": {
                "EMOM 15": {
                    1: {"DB Snatch": {"reps": "5/arm", "weight": "22.5/15kg"}},
                    2: {"Box Step-up": {"reps": 8, "height": "24/20inch"}},
                    3: {"Sit-up": {"reps": 12}}
                }
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Running", "Push-ups", "Toy Soldiers", "Scorpion Stretches"],
            "training_program": {
                "2 sets": {
                    "Running": {"distance": "200m", "pace": "slow"},
                    "Push-ups": {"reps": 10},
                    "Alternating Toy Soldiers": {"reps": 10},
                    "Alternating Scorpion Stretches": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Hand Release Push-ups", "Running", "Burpees"],
            "training_program": {
                "For Time": {
                    "A Hand Release Push-ups": {"reps": "9-15-21"},
                    "Running": {"distance": ["100m", "200m", "300m"]},
                    "B Hand Release Push-ups": {"reps": "9"}
                },
                "notes": "Complete full sequence"
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["PVC Pass-throughs", "Spiderman Stretches", "Push-ups", "Down Dogs"],
            "training_program": {
                "2 sets": {
                    "PVC Pass-throughs": {"reps": 10},
                    "Alternating Spiderman Stretches": {"reps": 10},
                    "Push-ups": {"reps": 5},
                    "Scap Pull-ups": {"reps": 5},
                    "Single-arm Dumbbell Shoulder Press": {"reps": 5, "notes": "each arm"}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Weighted Ab Mat Sit Up", "Assault Bike", "Double Unders"],
            "training_program": {
                "AMRAP 15": {
                    "Weighted Ab Mat Sit Up": {"reps": 20, "weight": "#20/#14 medball"},
                    "Assault Bike": {"calories": 12}
                }
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Jumping Jacks", "Push-ups", "PVC Front Squats", "PVC Overhead Squats"],
            "training_program": {
                "rounds": {
                    "Jumping Jacks": {"reps": 20},
                    "Push-ups": {"reps": 5},
                    "PVC Front Squats": {"reps": 10},
                    "PVC Overhead Squats": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Clean and Jerk Progression"],
            "training_program": {
                "technique": {
                    "Clean Pull": {"reps": 3},
                    "Power Clean": {"reps": 1},
                    "Clean and Jerk": {"reps": 1}
                }
            },
            "training_type": "warm-up",
            "training_time": 15
        }
    },
    {
        "metcon": {
            "exercises_used": ["Clean and Jerk", "Double Under"],
            "training_program": {
                "EMOM": {
                    "odd_minutes": {"Clean and Jerk": {"reps": 3, "notes": "touch and go"}},
                    "even_minutes": {"Double Under": {"reps": 30}},
                    "time": 15
                }
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },

    {
        "warm_up": {
            "exercises_used": ["PVC Switch", "Mountain Climbers", "Burpees", "Air Squats"],
            "training_program": {
                "rounds": {
                    "Mountain Climbers": {"reps": 20},
                    "Burpees": {"reps": 5},
                    "Air Squats": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["KB Swings", "Shuttle Runs"],
            "training_program": {
                "2 Rounds For Time": {
                    "KB Swings": {"reps": 50, "weight": "32/24kg"},
                    "Shuttle Runs": {"distance": "75M"}
                },
                "notes": "Partners split work as desired"
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Muscle Cleans", "Front Squats", "Push-ups", "Ring Rows"],
            "training_program": {
                "2 sets": {
                    "Hang Muscle Cleans": {"reps": 5},
                    "Front Squats": {"reps": 5},
                    "Push-ups": {"reps": 10},
                    "Ring Rows": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Dumbbell Walking Lunges", "Wall Walks", "AbMat Sit-ups"],
            "training_program": {
                "For Time": {
                    "DB Walking Lunges": {"reps": "20/leg", "weight": "22.5/15kg"},
                    "Wall Walks": {"reps": 2},
                    "AbMat Sit-ups": {"reps": 20}
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Leg Swings", "Good Mornings", "Romanian Deadlifts", "Jump Rope"],
            "training_program": {
                "rounds": {
                    "Leg Swings": {"reps": "10/leg"},
                    "Unweighted Good Mornings": {"reps": 10},
                    "Single-leg Romanian Deadlifts": {"reps": "5/leg"},
                    "Jump Rope": {"reps": 50}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Back Squat", "Pull-ups"],
            "training_program": {
                "Every 3 min x 5": {
                    "Back Squat": {"reps": "10-8-8-6-6", "notes": "Build in weight"},
                    "Pull-ups": {"reps": "Max effort"}
                }
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Running", "Shuttle Run", "Mountain Climbers", "Burpees", "Spiderman Stretches"],
            "training_program": {
                "2 rounds": {
                    "Running": {"distance": "100m", "pace": "moderate"},
                    "Mountain Climbers": {"reps": 30},
                    "PVC Snatch": {"reps": 10},
                    "Alternating Lunges": {"reps": 10},
                    "Up-downs": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Deadlift", "Hang Power Snatch", "Overhead Squat"],
            "training_program": {
                "10 Rounds": {
                    "Deadlift": {"reps": 4, "weight": "45/60kg"},
                    "Hang Power Snatch": {"reps": 3},
                    "Overhead Squat": {"reps": 2}
                }
            },
            "training_type": "metcon",
            "training_time": "20"
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Running", "Bear Crawl", "Samson Lunges", "Inchworm", "Burpee"],
            "training_program": {
                "movements": {
                    "Running": {"distance": "200m", "pace": "moderate"},
                    "Bear Crawl": {"distance": "75M"},
                    "Samson Lunges": {"distance": "75M"},
                    "Inchworm + Push-up": {"distance": "75M"},
                    "Burpee Broad Jump": {"distance": "75M"}
                }
            },
            "training_type": "warm-up",
            "training_time": 15
        }
    },
    {
        "metcon": {
            "exercises_used": ["Deadlift", "Power Snatch", "Overhead Squat"],
            "training_program": {
                "12 Rounds": {
                    "Deadlift": {"reps": 4, "weight": "45/60kg"},
                    "Hang Power Snatch": {"reps": 3},
                    "Overhead Squat": {"reps": 2}
                },

            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Row/Bike", "Single Unders", "Toy Soldiers", "Push-ups"],
            "training_program": {
                "3 rounds": {
                    "Row/Bike": {"calories": 10},
                    "Single Unders": {"reps": 50},
                    "Push-ups": {"reps": 10}
                },
                "rest": "30 sec between rounds"

            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Back Squat", "Air Squat"],
            "training_program": {
                "Every 3min x 5 sets": {
                    "Back Squat": {"scheme": "10-8-8-6-6"}
                },
                "notes": "start with light weight and build it up to @8 RPE"
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },

    {
        "metcon": {
            "exercises_used": ["AbMat Sit-ups", "Toes to Bar", "K2E"],
            "training_program": {
                "For Time": {
                    "AbMat Sit-ups": {"reps": 60},
                    "Toes to Bar": {"reps": 40},
                    "Knees to Elbows": {"reps": 20}
                },
                "rest": "2 min between rounds"

            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Running", "Down and Back Movements"],
            "training_program": {
                "movements": {
                    "Running": {"distance": "400m", "pace": "easy"},
                    "Bear Crawl": {"distance": "75M"},
                    "Samson Lunges": {"distance": "75M"},
                    "Crab Walk": {"distance": "75M"},
                    "Burpee Broad Jump": {"distance": "75M"}
                }
            },
            "training_type": "warm-up",
            "training_time": 15
        }
    },
    {
        "metcon": {
            "exercises_used": ["Strict Press", "Push-ups", "Box Step-ups"],
            "training_program": {
                "For Time": {
                    "round_scheme": "10-8-6-4",
                    "Strict Press": {"weight": "45/30kg"},
                    "Box Step-ups": {"height": "24/20inch"}
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Spiderman Stretches", "Toy Soldiers", "Single Leg V-ups"],
            "training_program": {
                "2 sets": {
                    "Alternating Spiderman Stretches": {"reps": 10},
                    "Toy Soldiers": {"reps": 10},
                    "Single Leg V-ups": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Double Unders", "Wall Ball", "Assault Bike"],
            "training_program": {
                "Every 3:00 for 5 rounds": {
                    "Double Unders": {"reps": 40},
                    "Wall Ball Shots": {"reps": 20, "weight": "20/14lbs"}
                },
                "rest": "remaining time"

            },
            "training_type": "metcon",
            "training_time": 15
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Up-downs", "PVC Good Mornings", "PVC Snatch"],
            "training_program": {
                "2 sets": {
                    "Up-downs": {"reps": 20},
                    "PVC Good Mornings": {"reps": 10},
                    "PVC Snatch Grip Behind-the-neck Press": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Running", "Samson Stretch", "Bear Crawl", "Push-ups"],
            "training_program": {
                "1 set": {
                    "Running 1": {"distance": "200m", "pace": "slow"},
                    "Samson Stretch": {"reps": "30 sec/side"},
                    "Bear Crawl": {"distance": "75M"},
                    "Push-ups": {"reps": "5-10"},
                    "Running 2": {"distance": "200m", "pace": "moderate"}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["DB Power Clean", "Ring Rows", "Box Jumps"],
            "training_program": {
                "On 12:00 Clock": {
                    "DB Power Clean": {"reps": "2-4-6-8-10", "weight": "22.5/15kg"},
                    "Ring Dips": {"reps": "4-8-12-16-20"},
                    "Double Unders": {"reps": "prescribed"}
                }
            },
            "training_type": "metcon",
            "training_time": 12
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Arm Circles", "Kettlebell Presses", "Goblet Squats", "Wall Walk"],
            "training_program": {
                "3 sets": {
                    "Arm Circles Forward": {"reps": 10},
                    "Arm Circles Backward": {"reps": 10},
                    "Single-arm KB Presses": {"reps": 5, "notes": "each arm"},
                    "Tempo Goblet Squat": {"reps": 5, "notes": "@3000 tempo"},
                    "Push-ups": {"reps": 5},
                    "Wall Walk": {"reps": 1}
                }
            },
            "training_type": "warm-up",
            "training_time": 15
        }
    },
    {
        "metcon": {
            "exercises_used": ["Back Squat", "Handstand Push-ups", "Box Jump"],
            "training_program": {
                "AMRAP 9:00": {
                    "exercises": {
                        "Back Squat": {"reps": "2-4-6-8", "notes": "@85-90%"},
                        "Handstand Push-ups": {"reps": "prescribed"},
                        "Box Jump": {"height": "60/50cm"}
                    }
                }
            },
            "training_type": "metcon",
            "training_time": 9
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Jog", "Samson Lunges", "Superman Hold", "Plank Reach Through"],
            "training_program": {
                "3 rounds": {
                    "Jog": {"distance": "200 M"},
                    "Samson Lunge Stretch": {"time": "0:30"},
                    "Superman Hold": {"time": "0:30"},
                    "Alternating Plank Reach Through": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 15
        }
    },
    {
        "metcon": {
            "exercises_used": ["Deadlift", "Knees-to-Elbows"],
            "training_program": {
                "In Team of 2": {
                    "AMRAP 2": {
                        "Knees-to-Elbows": {"reps": 40},
                        "Machine Distance": {"type": "row/bike/assault", "distance": "2500/3000"}
                    },
                    "notes": "One person works at a time during K2E, other holds plank"
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Plate Ground-to-Overhead", "Counterbalance Squats", "Ring Rows"],
            "training_program": {
                "2 sets": {
                    "Plate Ground-to-Overhead": {"reps": 10},
                    "Plate Counterbalance Squats": {"reps": 10},
                    "Ring Rows": {"reps": 10},
                    "Run": {"distance": "400m"}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Strict Pull-up", "Deadlift", "Wall Ball", "Farmers Carry"],
            "training_program": {
                "For Time": {
                    "Strict Pull-up 1": {"reps": 15},
                    "Deadlift 1": {"reps": 25, "weight": "100/70kg"},
                    "Wall Ball 1": {"reps": 50, "weight": "20/14lbs"},
                    "Farmers Carry": {"notes": "down stairs", "weight": "32/24kg"},
                    "Wall Ball 2": {"reps": 50},
                    "Deadlift 2": {"reps": 25},
                    "Strict Pull-up 2": {"reps": 15}
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "metcon": {
            "exercises_used": ["Assault Bike/Row", "Devil Press"],
            "training_program": {
                "4 Rounds": {
                    "Assault Bike/Row": {"calories": "100/80"},
                    "Devil Press": {"reps": 14, "weight": "22.5/15 kg"}
                },
                "rest": "2 min between rounds"
            },
            "training_type": "metcon",
            "training_time": 33
        }
    },
    {
        "metcon": {
            "exercises_used": ["Power Snatch", "Bar Facing Burpee"],
            "training_program": {
                "5 Rounds": {
                    "Power Snatch": {"reps": 5, "weight": "40/60kg"},
                    "Bar Facing Burpee": {"reps": 12}
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Row/Bike", "Single Unders", "Romanian Deadlift"],
            "training_program": {
                "3 sets": {
                    "Row/Bike": {"calories": 10},
                    "Single Unders": {"reps": 30},
                    "Romanian Deadlift": {"reps": 10, "weight": "empty barbell"}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Clean", "Push Press", "Box Jump"],
            "training_program": {
                "EMOM 16:00": {
                    "Odd Minutes": {"Clean + Push Press": {"reps": "3+3-6+6-9+9"}},
                    "Even Minutes": {"Box Jump": {"reps": 12, "height": "24/20inch"}}
                }
            },
            "training_type": "metcon",
            "training_time": 16
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Deadlift", "Bent Over Rows", "Air Squats"],
            "training_program": {
                "4 sets": {
                    "Deadlift": {"reps": 3},
                    "Bent Over Rows": {"reps": 10},
                    "Air Squats": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 15
        }
    },
    {
        "metcon": {
            "exercises_used": ["Deadlift", "Pull-ups", "Wall Ball"],
            "training_program": {
                "3 Sets x 4:00, 1:00 OFF": {
                    "Deadlift": {"reps": 7, "weight": "@70%"},
                    "Pull-ups": {"reps": 14}
                },
                "rest": "1 min between rounds"

            },
            "training_type": "metcon",
            "training_time": 15
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Jumping Jacks", "Air Squats", "Good Mornings", "Bent Over Rows"],
            "training_program": {
                "2 rounds": {
                    "Jumping Jacks": {"reps": 20},
                    "Air Squats": {"reps": 20},
                    "Good Mornings": {"reps": 20},
                    "Bent Over Rows": {"reps": 20}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Running", "Deadlift", "Pull-ups"],
            "training_program": {
                "3 Sets x 4:00, 1:00 OFF": {
                    "Run": {"distance": "200m"},
                    "Deadlift": {"reps": 7, "weight": "85/60kg"},
                    "Pull-ups": {"reps": 14}
                }
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Inchworms", "Walking Lunges", "Mountain Climbers"],
            "training_program": {
                "2 sets": {
                    "Inchworms": {"reps": 5},
                    "Walking Lunges": {"reps": 10},
                    "Mountain Climbers": {"reps": 10},
                    "Forward/Back Leg Swings": {"reps": "10 each leg"}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Walking Lunges", "Wall Walks", "AbMat Sit-ups"],
            "training_program": {
                "AMRAP 10": {
                    "Walking Lunges": {"reps": "20 alternating"},
                    "Wall Walks": {"reps": 2},
                    "AbMat Sit-ups": {"reps": 20}
                }
            },
            "training_type": "metcon",
            "training_time": 10
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Row/Bike", "Samson Stretch Lunges", "Step-ups", "Wall Ball"],
            "training_program": {
                "2 sets": {
                    "Row/Bike/Shuttle Run": {"time": "2 min"},
                    "Samson Stretch Lunges": {"reps": 5},
                    "Step-ups": {"reps": 10},
                    "Medball Squats": {"reps": 5},
                    "Wall Ball Shots": {"reps": 5}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Strict Pull-up", "Deadlift", "Wall Ball", "Farmers Carry"],
            "training_program": {
                "For Time": {
                    "Strict Pull-up": {"reps": 15},
                    "Deadlift": {"reps": 25, "weight": "100/70"},
                    "Wall Ball": {"reps": 50, "weight": "22/26kg"},
                    "Farmers Carry": {"distance": "down stairs", "weight": "32/24kg"}
                },
                "notes": "Repeat sequence in reverse"

            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["PVC Good Mornings", "PVC Overhead Lunges", "PVC Pass Throughs", "Scap Pull-ups"],
            "training_program": {
                "2 sets": {
                    "PVC Good Mornings": {"reps": 10},
                    "PVC Overhead Lunges": {"reps": 10},
                    "PVC Pass Throughs": {"reps": 10},
                    "Scap Pull-ups": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Deadlift", "Walking Lunges", "Wall Walks"],
            "training_program": {
                "AMRAP 10": {
                    "Deadlift": {"reps": 20, "weight": "70/47.5kg"},
                    "Walking Lunges": {"reps": "20 alternating"},
                    "Wall Walks": {"reps": 2}
                }
            },
            "training_type": "metcon",
            "training_time": 10
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Plate Ground-to-Overhead", "Plate Counterbalance Squats", "Ring Rows"],
            "training_program": {
                "2 sets": {
                    "Plate Ground-to-Overhead": {"reps": 10},
                    "Plate Counterbalance Squats": {"reps": 10},
                    "Ring Rows": {"reps": 10},
                    "Running": {"distance": "100m"}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Thruster", "Double Unders"],
            "training_program": {
                "For Time": {
                    "Double Unders": {"reps": 50},
                    "Thrusters": {"reps": 21, "weight": "30/42.5kg"}
                },
                "notes": "Repeat sequence in reverse"
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Single Unders", "Inch Worms", "Dumbbell Romanian Deadlifts", "Muscle Cleans"],
            "training_program": {
                "2 sets": {
                    "Single Unders": {"reps": 30},
                    "Inch Worms + Push-up": {"reps": 5},
                    "DB Romanian Deadlifts": {"reps": 10, "notes": "light weight"},
                    "DB Muscle Cleans": {"reps": 5, "notes": "each arm"}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Back Rack Lunge", "Ring Dips", "Double Unders"],
            "training_program": {
                "5 Rounds": {
                    "Back Rack Lunge": {"reps": "6-6-6-6", "weight": "85-90%"},
                    "Ring Dips": {"reps": "max effort"},
                    "Double Unders": {"reps": 50}
                }
            },
            "training_type": "metcon",
            "training_time": 25
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Jog", "Spiderman Stretches", "Samson Stretch", "KB Swing"],
            "training_program": {
                "1 set": {
                    "Alternating Jog": {"distance": "200m"},
                    "Spiderman Stretches": {"reps": 10},
                    "Forward/Backward KB Swings": {"reps": "20/20"},
                    "Samson Stretch": {"time": "30 sec/side"}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Power Clean", "Front Squat", "Bar Muscle Ups"],
            "training_program": {
                "7 Rounds For Time": {
                    "Power Cleans": {"reps": 10},
                    "Front Squats": {"reps": 10},
                    "Bar Muscle Ups": {"reps": 10}
                }
            },
            "training_type": "metcon",
            "training_time": 25
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Run", "Inchworm", "Air Squat", "DB Snatch", "Kip Swing"],
            "training_program": {
                "2 rounds": {
                    "Run": {"distance": "200m"},
                    "Inchworm + Push-up": {"reps": 5},
                    "Air Squat": {"reps": 10},
                    "DB Snatch": {"reps": 10},
                    "Kip Swing": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Power Clean", "Front Squat", "Push Jerk"],
            "training_program": {
                "Power Clean Progression": {
                    "Build to": {"goal": "1RM"},
                    "time": "16:00"
                }
            },
            "training_type": "strength",
            "training_time": 16
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Single Unders", "Samson Lunges", "Hollow Hold", "Scap Pull-up"],
            "training_program": {
                "3 rounds": {
                    "Single Unders": {"reps": 30},
                    "Samson Lunges": {"reps": "10/side"},
                    "Hollow Hold": {"time": "30 sec"},
                    "Scap Pull-up": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Kettlebell Swings", "Toe-to-bar"],
            "training_program": {
                "For Time": {
                    "Kettlebell Swings": {"reps": "15-12-9-6-3", "weight": "32/24kg"},
                    "Toes-to-bar": {"reps": "prescribed"}
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["PVC Pass-throughs", "Good Mornings", "Power Clean", "Plank Hold"],
            "training_program": {
                "2 sets": {
                    "PVC Pass-throughs": {"reps": 10},
                    "PVC Good Mornings": {"reps": 10},
                    "Side Plank Hold": {"time": "15 sec/side"},
                    "Power Clean": {"reps": 5, "notes": "build up"}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Power Clean", "Run", "Plank Hold"],
            "training_program": {
                "3 rounds for time": {
                    "Power Clean": {"reps": 21, "weight": "50/35kg"},
                    "Run": {"distance": "200m"},
                    "Plank Hold": {"time": "equal to run time"}
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Run", "Single Unders", "Samson Stretch"],
            "training_program": {
                "rounds": {
                    "Run": {"distance": "200m", "pace": "easy"},
                    "Single Unders": {"reps": 30},
                    "Samson Stretch": {"time": "20 sec/side"}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Cal Machine", "KB Swing"],
            "training_program": {
                "For Time": {
                    "Cal Machine": {"calories": "40-30-20", "type": "M/26-24-14 W"},
                    "Dual KB Swing": {"reps": "34-24-14", "weight": "24/16 or 22.5/15 kg"}}
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Air Squats", "Granny Tosses", "Chest Passes", "Side Tosses"],
            "training_program": {
                "1 round": {
                    "Air Squats": {"reps": 10},
                    "Granny Tosses": {"reps": 10},
                    "Chest Passes": {"reps": 10},
                    "Side Tosses": {"reps": "10/side"}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Wall Ball", "Ring Muscle-ups", "Burpees"],
            "training_program": {
                "AMRAP 25 with partner": {
                    "Wall Ball": {"reps": 20, "weight": "20/14lbs"},
                    "Ring Muscle-ups": {"reps": 10},
                    "Burpees": {"reps": 5}
                },
                "notes": "Partners split work as needed"
            },
            "training_type": "metcon",
            "training_time": 25
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Movement Drills", "Each drill 7.5M down and back"],
            "training_program": {
                "sequence": {
                    "Jog": {"distance": "down and back"},
                    "High Knees 1": {"distance": "7.5M each way"},
                    "Karaoke": {"distance": "7.5M each way"},
                    "Knee to Chest": {"distance": "7.5M each way"},
                    "Lunge with Torso Twist": {"distance": "7.5M each way"},
                    "High Knees 2": {"distance": "7.5M each way"},
                    "Butt Kickers": {"distance": "7.5M each way"}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Single-leg Squat"],
            "training_program": {
                "Mini Round": {
                    "Run": {"distance": "100m"},
                    "Single-leg Squats": {"reps": 12, "notes": "alternating"}
                },
                "notes": "Run together and perform 6 single-leg squats each"
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Samson Stretch Lunges", "PVC Work", "Ring Rows"],
            "training_program": {
                "2 sets": {
                    "Samson Stretch Lunges": {"reps": 10},
                    "PVC Overhead Squats": {"reps": 10},
                    "PVC Good Mornings": {"reps": 10},
                    "Ring Rows": {"reps": 10},
                    "Strict Pull-ups": {"reps": "3-5"}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Running", "Elbow to Instep", "Mountain Climbers"],
            "training_program": {
                "sequence": {
                    "Run": {"distance": "400M"},
                    "Elbow to Instep": {"reps": "5/side"},
                    "Mountain Climbers": {"reps": 20},
                    "Shoo the Turtles": {"reps": 20},
                    "Prisoner Squat": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Box Jump-overs", "Wall Ball", "Lateral Burpees"],
            "training_program": {
                "3 rounds": {
                    "Wall Ball Shots": {"reps": 50, "weight": "14/20lbs"},
                    "Lateral Burpee Box Jump-overs": {"reps": 50, "height": "40/50cm"}
                }
            },
            "training_type": "metcon",
            "training_time": 25
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Shuttle Run", "Step-ups", "Box Step-ups"],
            "training_program": {
                "2 sets": {
                    "Shuttle Run": {"pace": "easy"},
                    "Elbow to Instep": {"reps": 5},
                    "Box Step-ups": {"reps": 10},
                    "Jumping Air Squats": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Power Snatch", "Machine", "Box Step-ups"],
            "training_program": {
                "4 rounds for max reps": {
                    "Minute 1": {"exercise": "Snatches", "weight": "20/27.5"},
                    "Minute 2": {"exercise": "Machine for calories"},
                    "Minute 3": {"exercise": "Box Step-ups", "weight": "15/22.5"}
                },
                "rest": "1 min between rounds"

            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Jumping Jacks", "Air Squats", "Push-ups"],
            "training_program": {
                "2 sets": {
                    "Jumping Jacks": {"reps": 10},
                    "Air Squats": {"reps": 10},
                    "Push-ups": {"reps": 5},
                    "Box Jump-overs": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Wall Ball", "Burpee Box Jump-overs", "Plate Hold"],
            "training_program": {
                "3 rounds for time": {
                    "Wall Ball": {"reps": 50, "weight": "14/20lb"},
                    "Lateral Burpee Box Jump-overs": {"reps": 50, "height": "60/50cm"}
                },

            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Spiderman Stretches", "Leg Swings", "Jumping Jacks"],
            "training_program": {
                "1 set": {
                    "Spiderman Stretches": {"reps": 10},
                    "Leg Swings": {"reps": "10/leg", "notes": "across body"},
                    "Jumping Jacks": {"reps": 30}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Toes-to-Bar", "Wall Walks", "Knees-to-Elbows"],
            "training_program": {
                "3 rounds for time": {
                    "Toes-to-Bar": {"reps": 24},
                    "Wall Walks": {"reps": 8}
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Row/Bike", "Med Ball Passes", "Wall Ball"],
            "training_program": {
                "2 rounds": {
                    "Row/Bike": {"calories": 10},
                    "Med Ball Underhand Toss": {"reps": 10},
                    "Med Ball Side Passes": {"reps": "10/side"},
                    "Med Ball Squat + Throw": {"reps": 10}
                },
                "rest": "1 min between rounds"
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Power Clean", "Front Squat", "Push Jerk"],
            "training_program": {
                "For Time": {
                    "Power Clean": {"reps": 10},
                    "Front Squat": {"reps": 10},
                    "Push Jerk": {"reps": 10}
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Running", "Single Unders", "Spiderman Reaches"],
            "training_program": {
                "1 round": {
                    "Running": {"distance": "200m"},
                    "Single Unders": {"reps": 50},
                    "Spiderman Reaches": {"reps": 10},
                    "Push-ups": {"reps": 5},
                    "Box Step-ups": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Box Jump", "Push-ups", "Pull-ups"],
            "training_program": {
                "For Time": {
                    "Box Jump": {"reps": 20, "height": "60/50cm"},
                    "Push-ups": {"reps": 20},
                    "Pull-ups": {"reps": 20},

                }
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Med Ball Pass", "Underhand Toss", "Side Pass"],
            "training_program": {
                "2 sets with partner": {
                    "Med Ball Chest Pass": {"reps": 30},
                    "Med Ball Underhand Toss": {"reps": 30},
                    "Med Ball Side Pass": {"reps": "30/side"}
                },
                "rest": "20 sec between rounds"
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Power Clean", "Ring Muscle Up", "Box Jump"],
            "training_program": {
                "17:00 AMRAP": {
                    "Row": {"calories": 100},
                    "Lateral Burpee Box Jump": {"reps": 8},
                    "Power Clean": {"reps": "7.5%"}
                }
            },
            "training_type": "metcon",
            "training_time": 17
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Ring Rows", "Knee Push-ups", "Air Squats"],
            "training_program": {
                "1 set": {
                    "Ring Rows": {"reps": 10},
                    "Knee Push-ups": {"reps": 10},
                    "Air Squats": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        }
    },
    {
        "metcon": {
            "exercises_used": ["Wall Ball", "Strict Muscle-ups"],
            "training_program": {
                "For Time": {
                    "Wall Ball": {"reps": "50-40-30", "weight": "20/14lb"},
                    "Strict Muscle-ups": {"reps": "4-4-4"},

                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["PVC Switch Warm-up"],
            "training_program": {
                "Around 8 min": {
                    "Deadlift": {"time": "6:00-7:00", "notes": "build up"}
                }
            },
            "training_type": "warm-up",
            "training_time": 15
        }
    },
    {
        "metcon": {
            "exercises_used": ["Double Unders", "Deadlift"],
            "training_program": {
                "7 x 1:00 rounds": {
                    "Double Unders": {"reps": 21},
                    "Deadlift": {"reps": "max reps", "weight": "140/100kg"}
                },
                "rest": "2 min between rounds"
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },

    {
        "warm_up": {
            "exercises_used": ["Running", "Kettlebell Deadlifts", "Perfect Burpee"],
            "training_program": {
                "2 sets": {
                    "Running": {"distance": "200m", "notes": "slow/fast"},
                    "Kettlebell Deadlifts": {"reps": 10},
                    "Perfect Burpee": {"reps": 5}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        }
    },
    {
        "metcon": {
            "exercises_used": ["Toes to Bar", "Kettlebell Swings", "Running"],
            "training_program": {
                "3 sets for time": {
                    "Toes to Bar": {"reps": 10},
                    "Kettlebell Swings": {"reps": 10, "weight": "prescribed"},
                    "Running": {"distance": "200m"}
                },
                "rest": "3 min between sets"
            },
            "training_type": "metcon",
            "training_time": 20
        }
    }, {
        "warm_up": {
            "exercises_used": ["Jumping Jacks", "Walking Lunge", "Superman Arch", "Up-downs", "Jumping Squats"],
            "training_program": {
                "2 sets": {
                    "Jumping Jacks": {"reps": 20},
                    "Walking Lunge": {"reps": 20},
                    "Superman Arch": {"reps": 20},
                    "Up-downs": {"reps": 20},
                    "Jumping Squats": {"reps": 20}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Double-unders", "Wall Ball Shots", "Clean and Jerks"],
            "training_program": {
                "Every 5:00 for 30:00": {
                    "Run": {"distance": "200M"},
                    "Toes-to-Bar": {"reps": 8},
                    "Clean and Jerks": {"reps": 10, "weight": "60/40kg"}
                }
            },
            "training_type": "metcon",
            "training_time": 30
        }
    },
    {
        "metcon": {
            "exercises_used": ["Box Jump", "Sit-ups", "Ring Dips"],
            "training_program": {
                "25-20-15-10-5 reps for time": {
                    "Box Jump": {"height": "50/60 cm"},
                    "Sit-ups": {"reps": "same"},
                    "Ring Dips": {"reps": "same"}
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Run", "PVC Pass Throughs", "Good Mornings", "Overhead Squats"],
            "training_program": {
                "3 sets": {
                    "Run": {"distance": "200m"},
                    "PVC Pass Throughs": {"reps": 10},
                    "Good Mornings": {"reps": 10},
                    "Overhead Squats": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 15
        },
        "metcon": {
            "exercises_used": ["Power Clean", "Burpees", "Double-unders"],
            "training_program": {
                "AMRAP 12": {
                    "Power Clean": {"reps": 7, "weight": "60/40kg"},
                    "Burpees": {"reps": 7},
                    "Double-unders": {"reps": 40}
                }
            },
            "training_type": "metcon",
            "training_time": 12
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Single-unders", "Plank Up-downs", "DB Snatch", "KB Swings"],
            "training_program": {
                "2 sets": {
                    "Single-unders": {"reps": 50},
                    "Plank Up-downs": {"reps": 10},
                    "DB Snatch": {"reps": "10/arm", "weight": "light"},
                    "KB Swings": {"reps": 15, "weight": "light"}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        },
        "metcon": {
            "exercises_used": ["DB Farmers Carry", "Run", "Chest-to-bar Pull-ups"],
            "training_program": {
                "AMRAP 12": {
                    "DB Farmers Carry": {"distance": "50m", "weight": "15/22.5kg"},
                    "Run": {"distance": "100m"},
                    "Chest-to-bar Pull-ups": {"reps": 10}
                }
            },
            "training_type": "metcon",
            "training_time": 12
        }
    },
    {
        "warm_up": {
            "exercises_used": ["High Knees", "Mountain Climbers", "Push-ups", "Air Squats"],
            "training_program": {
                "3 rounds": {
                    "High Knees": {"reps": 20},
                    "Mountain Climbers": {"reps": 20},
                    "Push-ups": {"reps": 10},
                    "Air Squats": {"reps": 15}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Wall Ball", "Bar Muscle-ups"],
            "training_program": {
                "For Time": {
                    "Wall Ball": {"reps": "50-40-30", "weight": "20/14lb"},
                    "Bar Muscle-ups": {"reps": "5-4-3"},
                    "Time Cap": "20:00"
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Single-unders", "Single-under Jog", "Side-to-side", "Left Leg", "Right Leg",
                               "Double-unders"],
            "training_program": {
                "1 round": {
                    "Single-unders": {"reps": 30},
                    "Single-under Jog in Place": {"reps": 30},
                    "Single-under Jump Front to Back": {"reps": 30},
                    "Single-under Jump Side to Side": {"reps": 30},
                    "Single-under Left Leg": {"reps": 30},
                    "Single-under Right Leg": {"reps": 30},
                    "Double-unders or Attempts": {"reps": 30}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Run", "Double-DB Farmers Carry"],
            "training_program": {
                "5 Rounds": {
                    "Run": {"distance": "400m"},
                    "Double-DB Farmers Carry": {"distance": "50m", "weight": "22.5/15kg"}
                }
            },
            "training_type": "metcon",
            "training_time": 25
        }
    },
    {
        "warm_up": {
            "exercises_used": ["PVC Pass Throughs", "PVC Good Mornings", "PVC Overhead Squats", "Side Plank Hold",
                               "Run"],
            "training_program": {
                "2 sets": {
                    "PVC Pass Throughs": {"reps": 10},
                    "PVC Good Mornings": {"reps": 10},
                    "PVC Overhead Squats": {"reps": 10},
                    "Side Plank Hold": {"time": "15s/side"},
                    "Run": {"distance": "200m"}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        },
        "metcon": {
            "exercises_used": ["Power Cleans", "Box Jump Overs"],
            "training_program": {
                "Every 2:30 for 15:00": {
                    "Power Cleans": {"reps": 5, "weight": "60/40kg"},
                    "Box Jump Overs": {"reps": 5, "height": "24in"}
                }
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Arm Swings", "Arm Swings Overhead", "Torso Twists", "Toe Touches"],
            "training_program": {
                "1 set": {
                    "Arm Swings Across 1": {"reps": 10},
                    "Alternating Arm Swings Overhead": {"reps": 10},
                    "Arm Swings Across 2": {"reps": 10},
                    "Arm Swings Overhead": {"reps": 10},
                    "Torso Twists": {"reps": 10},
                    "Toe Touches": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 8
        },
        "metcon": {
            "exercises_used": ["Squat Clean", "Ring Dips"],
            "training_program": {
                "For Time": {
                    "Rounds": "21-15-9",
                    "Squat Clean": {"weight": "42.5/60kg"},
                    "Ring Dips": {"reps": "strict"},
                    "Time Cap": "10:00"
                }
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Inchworms", "Push-ups", "Hollow Rocks", "Tuck-ups", "V-ups"],
            "training_program": {
                "1 set": {
                    "Inchworms": {"reps": 5},
                    "Push-ups": {"reps": 5},
                    "Hollow Rocks": {"reps": 10},
                    "Tuck-ups": {"reps": 10},
                    "V-ups": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Handstand Walk", "Toes-to-Bar", "DB Snatches"],
            "training_program": {
                "For Time": {
                    "Handstand Walk": {"distance": "15M"},
                    "Toes-to-Bar": {"reps": 25},
                    "DB Snatches": {"reps": "50 alternating", "weight": "22.5/15kg"}
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Up-downs", "Band Pull-aparts", "Shoulder Taps", "PVC Pass Throughs"],
            "training_program": {
                "3 sets": {
                    "Up-downs": {"reps": 20},
                    "Band Pull-aparts": {"reps": 10},
                    "Shoulder Taps": {"reps": 20},
                    "PVC Pass Throughs": {"reps": 10}
                },
                "rest": "10 sec between movements"
            },
            "training_type": "warm-up",
            "training_time": 12
        },
        "metcon": {
            "exercises_used": ["Burpees", "DB Overhead Carry", "DB Suitcase Carry"],
            "training_program": {
                "AMRAP 10:00": {
                    "Burpees": {"reps": 20},
                    "DB Overhead Carry": {"distance": "100m", "weight": "single arm 22.5/15kg"},
                    "DB Suitcase Carry": {"distance": "100m", "weight": "22.5/15kg"}
                }
            },
            "training_type": "metcon",
            "training_time": 10
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Row/Bike", "Spiderman Stretches", "Push-ups", "Air Squats"],
            "training_program": {
                "1 set": {
                    "Row/Bike": {"cals": 12},
                    "Spiderman Stretches": {"reps": 5},
                    "Push-ups": {"reps": 10},
                    "Air Squats": {"reps": 10}
                },
                "Notes": "Light to moderate pace"
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Running", "Thrusters", "Pull-ups"],
            "training_program": {
                "For Time": {
                    "Run": {"distance": "1000M"},
                    "Thrusters": {"reps": 50, "weight": "15/20kg"},
                    "Pull-ups": {"reps": 30},
                    "Time Cap": "15:00"
                }
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Row/Bike/Shuttle Run", "Scap Pull-ups", "Push-ups", "Ring Rows"],
            "training_program": {
                "2 sets": {
                    "Row/Bike/Shuttle Run": {"time": "2:45"},
                    "Scap Pull-ups": {"reps": 15},
                    "Push-ups": {"reps": 10},
                    "Ring Rows": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        },
        "metcon": {
            "exercises_used": ["Double-unders", "Burpees", "Toes-to-bar"],
            "training_program": {
                "4 x AMRAP 3": {
                    "Double-unders": {"reps": 75},
                    "Burpees": {"reps": 25},
                    "Toes-to-bar": {"reps": "max"}
                },
                "rest": "1 min between AMRAPs"
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Band Pull-aparts", "Push-ups", "Air Squats", "Ring Rows", "Strict Pull-ups"],
            "training_program": {
                "3 sets": {
                    "Band Pull-aparts": {"reps": 10},
                    "Push-ups": {"reps": 5},
                    "Air Squats": {"reps": 10},
                    "Ring Rows or Strict Pull-ups": {"reps": "5-10"}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Wall Ball Shots", "Toes-to-bar", "Box Jumps"],
            "training_program": {
                "AMRAP 15": {
                    "Wall Ball Shots": {"reps": 10, "weight": "20/14lb"},
                    "Toes-to-bar": {"reps": 10},
                    "Box Jumps": {"reps": 10, "height": "50/40cm"}
                },
                "Notes": "Step down from box"
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Jumping Jacks", "Samson Lunges", "Over-the-fences", "Push-ups"],
            "training_program": {
                "2 sets": {
                    "Jumping Jacks": {"reps": 10},
                    "Over-the-fences": {"reps": 10},
                    "Samson Lunges": {"reps": 10},
                    "Push-ups": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Run", "Wall Ball Shots", "Double-unders", "T2B"],
            "training_program": {
                "4 x 2-minute rounds": {
                    "Run": {"distance": "45m"},
                    "Double-unders": {"reps": 24},
                    "Wall Ball Shots": {"reps": "max"}
                },
                "rest": "2 min between rounds"
            },
            "training_type": "metcon",
            "training_time": 16
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Bear Crawl", "Samson Lunges", "Side Lunges", "Crab Walk", "Burpee Broad Jump"],
            "training_program": {
                "Complete Distance": {
                    "Bear Crawl": {"distance": "7.5M"},
                    "Samson Lunges": {"distance": "7.5M"},
                    "Side Lunges": {"distance": "7.5M"},
                    "Crab Walk": {"distance": "7.5M", "notes": "high hips"},
                    "Burpee Broad Jump": {"distance": "7.5M"}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["KB Swings", "Shuttle Runs"],
            "training_program": {
                "2 rounds for time": {
                    "KB Swings": {"reps": 50, "weight": "24/32kg"},
                    "Shuttle Runs": {"reps": 50, "distance": "7.5M down/back"}
                },
                "Notes": "One partner works at a time"
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Single-unders", "PVC Pass Throughs", "Good Mornings", "Overhead Squats"],
            "training_program": {
                "2 sets": {
                    "Single-unders": {"reps": 30},
                    "PVC Pass Throughs": {"reps": 10},
                    "Good Mornings": {"reps": 10},
                    "Overhead Squats": {"reps": 10},
                    "Hold": {"time": "2s at bottom of each squat"}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        },
        "metcon": {
            "exercises_used": ["Row/Assault Bike", "DB Clean and Jerk"],
            "training_program": {
                "In Teams of 2": {
                    "Row": {"distance": "2000m", "or": "5000M Assault"},
                    "DB Clean and Jerk": {"reps": 100, "weight": "22.5/15kg"}
                },
                "Notes": "Partners split work as desired"
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Med Ball Chest Passes", "Bounce Passes", "Box Step-ups", "Squat Jumps"],
            "training_program": {
                "3 sets": {
                    "Med Ball Chest Passes": {"reps": 5},
                    "Med Ball Bounce Passes": {"reps": 5},
                    "Box Step-ups": {"reps": 10, "notes": "alternating"},
                    "Squat Jumps": {"reps": 10, "notes": "with partner"}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Wall Ball Shots", "Sumo Deadlift High Pulls", "Box Jumps", "Push Press", "Row/Bike"],
            "training_program": {
                "8 rounds for reps": {
                    "Wall Ball Shots": {"time": "1:30", "weight": "4/9kg"},
                    "Sumo Deadlift High Pulls": {"time": "1:30", "weight": "25/35kg"},
                    "Box Jumps": {"time": "1:30", "height": "60/50cm"},
                    "Push Press": {"time": "1:30", "weight": "25/35kg"},
                    "Row/Bike": {"time": "1:30", "for": "calories"}
                },
                "rest": "1.30 min between rounds"
            },
            "training_type": "metcon",
            "training_time": 24
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Row/Bike", "Band Pull-aparts", "Hollow Rocks", "Superman Hold", "Ring Rows",
                               "Pull-ups"],
            "training_program": {
                "1 set": {
                    "Row/Bike": {"cals": 10},
                    "Band Pull-aparts": {"reps": 15},
                    "Hollow Rocks": {"reps": 10},
                    "Superman Hold": {"time": "10s"},
                    "Ring Rows": {"reps": 10},
                    "Pull-ups": {"reps": "5-10"}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        },
        "metcon": {
            "exercises_used": ["Deadlifts", "Handstand Push-ups"],
            "training_program": {
                "For Time": {
                    "Deadlifts": {"reps": 45, "weight": "70/100kg"},
                    "Handstand Push-ups": {"reps": 45},
                    "Time Cap": "20:00"
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Single-unders", "Mountain Climbers", "Up-downs", "Kip Swings"],
            "training_program": {
                "3 sets": {
                    "Single-unders": {"reps": 20},
                    "Mountain Climbers": {"reps": 20},
                    "Up-downs": {"reps": 20},
                    "Kip Swings": {"reps": 10}
                },
                "rest": "30 sec between rounds"
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Row/Assault Bike", "DB Thrusters", "Toes-to-Bar"],
            "training_program": {
                "AMRAP 90s x 4": {
                    "Row/Assault Bike": {"cals": "16/12 Cal C2 | 12/10 Cal Assault"},
                    "DB Thrusters": {"reps": 8, "weight": "22.5/15kg"},
                    "Toes-to-Bar": {"reps": "Max"}
                },
                "rest": "1.30 min between rounds"
            },
            "training_type": "metcon",
            "training_time": 12
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Samson Stretches", "Hip Taps", "Scap Push-ups", "Mountain Climbers", "Air Squats"],
            "training_program": {
                "2 rounds": {
                    "Samson Stretches": {"reps": "10/side"},
                    "Hip Taps": {"reps": 20},
                    "Scap Push-ups": {"reps": 10},
                    "Mountain Climbers": {"reps": 20},
                    "Air Squats": {"reps": 15}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Run", "Power Cleans", "Burpees"],
            "training_program": {
                "EMOM 21": {
                    "Odd Minutes": {"Run": {"distance": "200M"}},
                    "Even Minutes": {"Power Clean": {"reps": 7, "weight": "60/40kg"}},
                    "Every Third Minute": {"Burpees": {"reps": 7}}
                }
            },
            "training_type": "metcon",
            "training_time": 21
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Jog", "Alternating Toe Touches", "Walking Lunges", "Inch Worms"],
            "training_program": {
                "1 round": {
                    "Jog": {"distance": "400M"},
                    "Alternating Toe Touches": {"reps": "10/leg"},
                    "Walking Lunges": {"steps": 20},
                    "Inch Worms": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Assault Bike/Row", "Wall Ball Shots", "Handstand Push-ups"],
            "training_program": {
                "5 Rounds": {
                    "Assault Bike/Row": {"work": "1:00 On", "rest": "1:00 Off"},
                    "Wall Ball Shots": {"reps": "Max in remaining time", "weight": "20/14lb"},
                    "Handstand Push-ups": {"reps": "Max in remaining time"}
                }
            },
            "training_type": "metcon",
            "training_time": 20
        }
    },
    {
        "warm_up": {
            "exercises_used": ["PVC Pass Throughs", "Good Mornings", "Shoulder Taps", "Ring Rows"],
            "training_program": {
                "2 sets": {
                    "PVC Pass Throughs": {"reps": 15},
                    "Good Mornings": {"reps": 15},
                    "Shoulder Taps": {"reps": "10/side"},
                    "Ring Rows": {"reps": 12}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Bar Muscle-ups", "Power Snatches", "Box Jump Overs"],
            "training_program": {
                "Every 2:00 for 12:00": {
                    "Bar Muscle-ups": {"reps": 3},
                    "Power Snatches": {"reps": 6, "weight": "42.5/30kg"},
                    "Box Jump Overs": {"reps": 12, "height": "24/20in"}
                }
            },
            "training_type": "metcon",
            "training_time": 12
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Single-unders", "Plank Hold", "KB Deadlifts", "DB Snatches"],
            "training_program": {
                "2 rounds": {
                    "Single-unders": {"reps": 50},
                    "Plank Hold": {"time": "30s"},
                    "KB Deadlifts": {"reps": 15},
                    "DB Snatches": {"reps": "5/arm"}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        },
        "metcon": {
            "exercises_used": ["Double-unders", "Power Clean and Jerks"],
            "training_program": {
                "For Time": {
                    "Double-unders": {"scheme": "50-40-30"},
                    "Power Clean and Jerks": {"scheme": "4-8-12", "weight": "42.5/60kg"}
                }
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Jumping Jacks", "Push-ups", "Prisoner Squat", "Box Jumps", "Burpee Box Jump Overs"],
            "training_program": {
                "2 sets": {
                    "Band Pull-aparts": {"reps": 30},
                    "Push-ups": {"reps": 10},
                    "Prisoner Squat": {"reps": "5-10"},
                    "Box Jumps": {"reps": 10, "height": "60/50cm"},
                    "Burpee Box Jump Overs": {"reps": 5}
                }
            },
            "training_type": "warm-up",
            "training_time": 12
        },
        "metcon": {
            "exercises_used": ["Chest-to-bar Pull-ups", "Burpee Box Jump-overs"],
            "training_program": {
                "Complete as many reps as possible": {
                    "2 Chest-to-bar Pull-ups": {"reps": 2},
                    "2 Burpee Box Jump-overs": {"reps": 2},
                    "4 Chest-to-bar Pull-ups": {"reps": 4},
                    "4 Burpee Box Jump-overs": {"reps": 4},
                    "6 Chest-to-bar Pull-ups": {"reps": 6}
                },
                "Notes": "Continue adding 2 reps to each movement"
            },
            "training_type": "metcon",
            "training_time": 15
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Single-leg KB Deadlifts", "Reverse Lunges", "Single-unders", "KB Good Mornings"],
            "training_program": {
                "1 set": {
                    "Single-leg KB Deadlifts": {"reps": "10/leg"},
                    "Alternating Reverse Lunges": {"reps": 20},
                    "Single-unders": {"reps": 40},
                    "KB Good Mornings": {"reps": 10}
                }
            },
            "training_type": "warm-up",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Double-unders", "Box Step-ups", "KB Swings"],
            "training_program": {
                "5 rounds for time": {
                    "Double-unders": {"reps": 40},
                    "Box Step-up": {"reps": 20, "height": "50/60cm"},
                    "KB Swings": {"reps": 20, "weight": "24/32kg"}
                }
            },
            "training_type": "metcon",
            "training_source": "rocklee",
            "training_time": 20
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Single-unders", "Mountain Climbers", "Superman Hold", "Up-downs", "Wall Walk"],
            "training_program": {
                "2 sets": {
                    "Single-unders": {"reps": 20},
                    "Mountain Climbers": {"reps": 20},
                    "Superman Hold": {"time": "20s"},
                    "Up-downs": {"reps": 20},
                    "Wall Walk": {"reps": 2}
                }
            },
            "training_type": "warm-up",
            "training_source": "rocklee",
            "training_time": 12
        },
        "metcon": {
            "exercises_used": ["DB Box Step-ups", "Power Clean", "Burpee Pull-ups"],
            "training_program": {
                "EMOM 15": {
                    "Minute 1": {"DB Box Step-ups": {"reps": 8, "weight": "22.5/15kg"}},
                    "Minute 2": {"Power Clean": {"reps": 3, "weight": "60/40kg"}},
                    "Minute 3": {"Burpee Pull-ups": {"reps": 6}}
                }
            },
            "training_type": "metcon",
            "training_source": "rocklee",
            "training_time": 15
        }
    },
    {
        "warm_up": {
            "exercises_used": ["Run", "Bear Crawl", "Samson Lunges", "Spiderman Twist", "Inchworm"],
            "training_program": {
                "1 round": {
                    "Run": {"distance": "200m", "pace": "moderate"},
                    "Bear Crawl": {"distance": "7.5M"},
                    "Samson Lunges": {"distance": "7.5M"},
                    "Spiderman Twist": {"distance": "7.5M"},
                    "Inchworm + Push-up": {"distance": "7.5M"}
                }
            },
            "training_type": "warm-up",
            "training_source": "rocklee",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Cal Row/Assault Bike", "DB Front Rack Walking Lunges"],
            "training_program": {
                "10 rounds": {
                    "Cal Row/Assault Bike": {"work": "30s On", "rest": "30s Off"},
                    "DB Weight": {"weight": "22.5/15kg per hand"}
                },
                "Notes": "During rest perform max DB Front Rack Walking Lunges"
            },
            "training_type": "metcon",
            "training_source": "rocklee",
            "training_time": 20
        }
    },
    {
        "warm_up": {
            "exercises_used": ["PVC Pass Throughs", "Overhead Lunges", "Good Mornings", "Side Plank"],
            "training_program": {
                "2 sets": {
                    "PVC Pass Throughs": {"reps": 15},
                    "PVC Overhead Lunges": {"reps": 10},
                    "PVC Good Mornings": {"reps": 15},
                    "Side Plank": {"time": "30s/side"}
                }
            },
            "training_type": "warm-up",
            "training_source": "rocklee",
            "training_time": 10
        },
        "metcon": {
            "exercises_used": ["Power Snatch", "Bar-facing Burpees"],
            "training_program": {
                "On a 15:00 Clock": {
                    "Power Snatches": {"reps": 75, "weight": "25/35kg"},
                    "Bar-facing Burpees": {"reps": "1 after every 5 snatches"}
                }
            },
            "training_type": "metcon",
            "training_source": "rocklee",
            "training_time": 15
        }
    },
    {
        "exercises_used": ["Running", "Bear Crawl", "Samson Lunges", "Spiderman Twist", "Inchworm", "Crab Walk",
                           "Burpee Broad Jump", "High Knees", "Butt Kickers"],
        "training_program": {
            "2 sets": {
                "Running": {"distance": "200m", "pace": "moderate"},
                "Bear Crawl": {"distance": "7.5M"},
                "Samson Lunges": {"distance": "7.5M"},
                "Spiderman Twist": {"distance": "7.5M"},
                "Inchworm + Push-up": {"distance": "7.5M"},
                "Crab Walk": {"distance": "7.5M"},
                "Burpee Broad Jump": {"distance": "7.5M"},
                "High Knees": {"distance": "7.5M"},
                "Butt Kickers": {"distance": "7.5M"}
            },
            "notes": ["Focus on maintaining high hips in crab walk", "Control movement speed"]
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Devil Press", "Running", "Row/Bike"],
        "training_program": {
            "8 rounds with a partner": {
                "Devil Press": {"reps": 6, "weight": "22.5/15kg"},
                "Running": {"distance": "200m"},
                "Row/Bike": {"notes": "Max Calories"}
            },
            "notes": ["One partner runs and devil press while other rows/bikes for max calories",
                      "Switch when runner returns",
                      "Each partner will run and row four times"]
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 25
    },
    {
        "exercises_used": ["Single Unders", "Inchworm", "Romanian Deadlifts", "DB Hang Clean", "DB Shoulder Press",
                           "DB Reverse Lunge"],
        "training_program": {
            "2 sets": {
                "Single Unders": {"reps": 30},
                "Inchworm + Push-up": {"reps": 5},
                "DB Romanian Deadlifts": {"reps": 10, "weight": "light"},
                "DB Hang Clean": {"reps": "5/arm"},
                "DB Shoulder Press": {"reps": "5/arm"},
                "DB Reverse Lunge": {"reps": "5/leg"}
            },
            "notes": "Build to working weight across sets"
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Back Rack Lunge"],
        "training_program": {
            "For Load": {
                "Back Rack Lunge": {"reps": "6-6-6-6-6"},
                "notes": ["Sub Max reps on last set",
                          "Find heavy set for the day, about @2RIR",
                          "From the rig"]
            }
        },
        "training_type": "strength",
        "training_time": 15
    },
    {
        "exercises_used": ["Hang Power Clean", "Ring Dips", "Double Unders"],
        "training_program": {
            "On a 12:00 clock": {
                "round_target": {
                    "DB Hang Power Clean": {"reps": "2-4-6-8-10", "weight": "15/22.5kg"},
                    "Ring Dips": {"reps": "4-8-12-16-20"},
                    "Double Unders": {"reps": "prescribed"}
                }
            },
            "notes": "Use two dumbbells"
        },
        "training_type": "metcon",
        "training_time": 12
    },
    {
        "exercises_used": ["Row/Bike", "Samson Stretch", "Step-ups", "Med Ball Squats", "Wall Ball"],
        "training_program": {
            "2 sets": {
                "Row/Bike": {"calories": 10},
                "Samson Stretch Lunges": {"reps": 5},
                "Step-ups": {"reps": 10},
                "Med Ball Squats": {"reps": 5},
                "Wall Ball": {"reps": 5}
            }
        },
        "training_type": "warm-up",
        "training_time": 12
    },
    {
        "exercises_used": ["Strict Pull-up", "Deadlift"],
        "training_program": {
            "Skill Progression and Workout Prep": {
                "Deadlift": {
                    1: {"Up Downs": {"reps": 8}},
                    2: {"Farmer Carry Hold": {"time": "20 sec", "notes": "workout load"}},
                    3: {"Deadlift": {"reps": 5}},
                    "notes": ["Rest 1:00 between sets", "Build to workout load"]
                }
            }
        },
        "training_type": "strength",
        "training_time": 15
    },
    {
        "exercises_used": ["Strict Pull-up", "Deadlift", "Wall Ball"],
        "training_program": {
            "For Time": {
                "round_target": {
                    "Strict Pull-up": {"reps": 15},
                    "Deadlift": {"reps": 25, "weight": "100/70kg"},
                    "Wall Ball": {"reps": 50, "weight": "20/14lbs"},
                    "Farmers Carry": {"distance": "down stairs", "weight": "32/24kg"},
                    "Wall Ball 2": {"reps": 50, "weight": "20/14lbs"},
                    "Deadlift 2": {"reps": 25, "weight": "100/70kg"},
                    "Strict Pull-up 2": {"reps": 15}
                }
            },
            "notes": ["Time cap 20:00"]
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },
    {
        "exercises_used": ["PVC Good Mornings", "PVC Overhead Lunges", "PVC Pass Throughs", "Jump Rope",
                           "Scorpion Stretches"],
        "training_program": {
            "2 sets": {
                "PVC Good Mornings": {"reps": 10},
                "PVC Overhead Lunges": {"reps": 10},
                "PVC Pass Throughs": {"reps": 10},
                "Jump Rope": {"reps": 30}
            },
            "notes": "10 sec between movements"
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Power Snatch"],
        "training_program": {
            "On a 6:00 clock": {
                1: {"Power Snatch": {"reps": 10}},
                2: {"Power Snatch": {"reps": 8}},
                3: {"Power Snatch": {"reps": 5}},
            },
            "notes": ["All unbroken sets WITHOUT pausing", "Build weight across sets"],
            "rest": "1:00-1:30 between sets"
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Power Snatch"],
        "training_program": {
            "Randy": {
                "For Time": {
                    "round_target": {
                        "Power Snatch": {"reps": 75, "weight": "25/35kg"}
                    }
                },
                "notes": ["10:00 time cap", "Scale weight as needed"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Single Unders", "Push-ups", "Toy Soldiers", "Scorpion Stretches"],
        "training_program": {
            "2 rounds": {
                "Single Unders": {"reps": 30},
                "Push-ups": {"reps": 10},
                "Toy Soldiers": {"reps": 10},
                "Scorpion Stretches": {"reps": 10}
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Wall Ball", "Pull-up", "Clean"],
        "training_program": {
            "Skill Progression": {
                "Clean & Wall Ball Prep": {
                    1: {"Wall Ball": {"reps": 5}},
                    2: {"Pull-up": {"reps": "5 strict"}},
                    3: {"Clean": {"reps": 3, "notes": "technique focus"}},
                    "notes": ["Build to working weight", "Focus on positions"]
                }
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Double Unders", "Wall Ball", "Assault Bike"],
        "training_program": {
            "Every 3:00 for 5 rounds": {
                "Double Unders": {"reps": 40},
                "Wall Ball": {"reps": 20, "weight": "20/14lbs"}
            },
            "notes": "Rest remaining time",
            "rest": "remaining time in the 3:00"
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Up-downs", "PVC Good Mornings", "PVC Snatch"],
        "training_program": {
            "2 sets": {
                "Up-downs": {"reps": 20},
                "PVC Good Mornings": {"reps": 10},
                "PVC Snatch Grip Behind-the-neck Press": {"reps": 10}
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Power Clean", "Running"],
        "training_program": {
            "Power Clean Progression": {
                "Every 1 min x 9 sets": {
                    "sets": "5-5-3-3-3-1-1-1-1",
                    "notes": ["Build it up to heavy single", "Focus on speed under bar"]
                }
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["DB Power Clean", "Ring Rows", "Box Jumps"],
        "training_program": {
            "On 12:00 Clock": {
                "DB Power Clean": {"reps": "2-4-6-8-10", "weight": "22.5/15kg"},
                "Ring Dips": {"reps": "4-8-12-16-20"},
                "Double Unders": {"reps": "prescribed"}
            },
            "notes": ["Progress through all reps within time cap"]
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Spiderman Stretch", "Up Downs", "PVC Pass Through", "Air Squat", "PVC Shoulder Press"],
        "training_program": {
            "rounds": {
                "round_target": {
                    "Alternating Spiderman Stretch": {"reps": 30},
                    "Up Downs": {"reps": 20},
                    "PVC Pass Through": {"reps": 20},
                    "Air Squat": {"reps": 20},
                    "PVC Shoulder Press": {"reps": 30}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Thruster"],
        "training_program": {
            "Progression": {
                "round_target": {
                    "Thruster": {"reps": 5, "notes": "Build to heavy 3-rep thruster from the rack"}
                }
            }
        },
        "training_type": "skill",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Rope Climb", "Thruster"],
        "training_program": {
            "For Time": {
                "round_target": {
                    "Rope Climb": {"reps": 1},
                    "Thruster": {"reps": "3-9", "weight": "35/50kg"}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },
    {
        "exercises_used": ["Jumping Jacks", "Samson Lunges", "Kettlebell Bent Over Row", "Air Squat",
                           "Kettlebell Sumo Deadlift"],
        "training_program": {
            "rounds": {
                "round_target": {
                    "Jumping Jacks": {"reps": 20},
                    "Samson Lunges": {"reps": 20},
                    "Kettlebell Bent Over Row": {"reps": 20},
                    "Air Squat": {"reps": 20},
                    "Kettlebell Sumo Deadlift": {"reps": 20}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Deadlift"],
        "training_program": {
            "build": {
                "round_target": {
                    "Deadlift": {"reps": 3, "notes": "Build to heavy set of 3"}
                },
                "rest": "1:00-2:00 between lifts"
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 20
    },
    {
        "exercises_used": ["Running", "Deadlift", "Sit Up"],
        "training_program": {
            "3 Sets": {
                "4:00 ON / 1:00 OFF": {
                    "Running": {"distance": "200m", "pace": "@85% RPE"},
                    "round_target": {
                        "Deadlift": {"reps": 7},
                        "Sit Up": {"reps": 14}
                    }
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Row", "Single Under", "Kettlebell Romanian Deadlift"],
        "training_program": {
            "3 sets": {
                "round_target": {
                    "Row": {"calories": 10},
                    "Single Under": {"reps": 30},
                    "Kettlebell Romanian Deadlift": {"reps": 10}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    }, {
        "exercises_used": ["Clean", "Push Press", "Box Jump"],
        "training_program": {
            "EMOM 16": {
                "odd_minutes": {
                    "Clean + Push Press": {"reps": "3+3-6+6-9+9"}
                },
                "even_minutes": {
                    "Box Jump": {"reps": 12, "height": "24/20inch"}
                }
            }
        },
        "training_type": "skill",
        "training_source": "rocklee",
        "training_time": 16
    }, {
        "exercises_used": ["Devil Press", "Running"],
        "training_program": {
            "4 Rounds": {
                "round_target": {
                    "Devil Press": {"reps": 14, "weight": "22.5/15kg"},
                    "Running": {"distance": "200m"}
                },
                "rest": "2:00 between rounds"
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 33
    }, {
        "exercises_used": ["Running", "Spiderman Stretch", "Single Leg V-up", "Scap Pull-up"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "Running": {"distance": "200m"},
                    "Alternating Spiderman Stretch": {"reps": 10},
                    "Single Leg V-up": {"reps": 10},
                    "Scap Pull-up": {"reps": 10}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    }, {
        "exercises_used": ["Toes to Bar", "Wall Walk"],
        "training_program": {
            "AMRAP 10": {
                "round_target": {
                    "Toes to Bar": {"reps": "3-6-9-12"},
                    "Wall Walk": {"reps": "1-2-3-4"}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 10
    }, {
        "exercises_used": ["Single Under", "Jump Rope Variations"],
        "training_program": {
            "rounds": {
                "round_target": {
                    "Single Under": {"reps": 30},
                    "Jump Rope Variations": {
                        "Jog in Place": {"reps": 20},
                        "Jump Front to Back": {"reps": 20},
                        "Jump Side to Side": {"reps": 20},
                        "Left Leg": {"reps": 20},
                        "Right Leg": {"reps": 20}
                    }
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 8
    }, {
        "exercises_used": ["Deadlift", "Hang Power Clean", "Front Squat"],
        "training_program": {
            "For Time": {
                "round_target": {
                    "Deadlift": {"reps": "7-7-5", "weight": "62.5/45kg"},
                    "Hang Power Clean": {"reps": "prescribed"},
                    "Front Squat": {"reps": "prescribed"}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 8
    }, {
        "exercises_used": ["PVC Good Morning", "PVC Overhead Lunge", "PVC Pass Through", "Mountain Climber",
                           "Air Squat"],
        "training_program": {
            "rounds": {
                "round_target": {
                    "PVC Good Morning": {"reps": 10},
                    "PVC Overhead Lunge": {"reps": 10},
                    "PVC Pass Through": {"reps": 10},
                    "Mountain Climber": {"reps": 20},
                    "Air Squat": {"reps": 10}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    }, {
        "exercises_used": ["Power Clean", "Bar Muscle Up", "Box Jump"],
        "training_program": {
            "Every 2 min x 10": {
                "round_target": {
                    "Power Clean": {"reps": 3, "weight": "60/40kg"},
                    "Bar Muscle Up": {"reps": 2},
                    "Box Jump": {"reps": 5, "height": "30/24inch"}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },
    {
        "exercises_used": ["Toes to Bar", "Knees to Elbows"],
        "training_program": {
            "Progression": {
                "round_target": {
                    "1 set": {
                        "Synchronized Sit-ups": {"reps": 5},
                        "Calories 1": {"reps": "15/20"},
                        "Toes to Bar": {"reps": 5},
                        "Calories 2": {"reps": "15/20"},
                        "Strict Knees to Elbows": {"reps": 3}
                    }
                }
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 20
    }, {
        "exercises_used": ["AbMat Sit-up", "Row", "Toes to Bar", "Knees to Elbows"],
        "training_program": {
            "For Time with Partner": {
                "round_target": {
                    "AbMat Sit-up": {"reps": 60, "notes": "synchronized"},
                    "Row 1": {"calories": "40-50"},
                    "Toes to Bar": {"reps": 40},
                    "Row 2": {"calories": "40-50"},
                    "Strict Knees to Elbows": {"reps": 20}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    }, {
        "exercises_used": ["Row", "Single Under", "Turkish Get-Up", "Push-up", "Spiderman Stretch"],
        "training_program": {
            "3 rounds": {
                "row/bike/shuttle run": {"time": "1:00"},
                "round_target": {
                    "Single Under": {"reps": 20},
                    "Turkish Get-Up": {"reps": 10},
                    "Push-up": {"reps": 10},
                    "Spiderman Stretch": {"reps": 10},
                    "Step-ups": {"reps": 10},
                    "Samson Stretch": {"reps": "30/side"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 15
    }, {
        "exercises_used": ["Back Squat"],
        "training_program": {
            "Every 3min x 5 sets": {
                "round_target": {
                    "Back Squat": {
                        "scheme": "10-8-8-6-6",
                        "notes": ["Start with light weight", "Build it up to @8 RPE", "Moderate weight"]
                    }
                }
            }
        },
        "training_type": "strength",
        "training_time": 20
    }, {
        "exercises_used": ["Box Jump", "Running", "KB Swing"],
        "training_program": {
            "AMRAP 10": {
                "round_target": {
                    "Box Jump": {"height": "50/40 cm"},
                    "Running": {"distance": "10m"},
                    "KB Swing": {"weight": "32/24 kg"},
                },
                "notes": ["Step down from the box", "Use two KBs"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Muscle Clean", "Front Squat", "Push-up", "Ring Row"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "Muscle Clean": {"reps": 5, "notes": "Empty barbell"},
                    "Front Squat": {"reps": 5},
                    "Push-up": {"reps": 10},
                    "Ring Row": {"reps": 10}
                },
                "notes": ["Focus on technique and proper positioning"]
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Front Squat"],
        "training_program": {
            "technique": {
                "Front Squat": {
                    "progression": [
                        {"reps": "3-5", "notes": "Build to working weight"},
                        {"notes": "Rest 1:00 between sets"},
                        {"notes": "Front squat from the Rig/Floor"}
                    ]
                }
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Front Squat", "Pull-up"],
        "training_program": {
            "EMOM 20": {
                "round_target": {
                    "odd_minutes": {"Front Squat": {"reps": 5, "weight": "80/50kg"}},
                    "even_minutes": {"Pull-up": {"reps": 5, "notes": "jumping muscle-up if scaled"}}
                },
                "notes": ["Keep core tight throughout front squats", "Focus on strict form"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },
    {
        "exercises_used": ["Toe Touch", "Good Morning", "Deadlift", "Behind Neck Press", "Burpee"],
        "training_program": {
            "2 rounds": {
                "round_target": {
                    "Toe Touch": {"reps": 10},
                    "Good Morning": {"reps": 10, "notes": "Unweighted"},
                    "Deadlift": {"reps": 10, "notes": "Empty barbell"},
                    "Behind Neck Press": {"reps": 10},
                    "Burpee": {"reps": 30}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Power Snatch", "Overhead Squat"],
        "training_program": {
            "Build up": {
                "round_target": {
                    "Power Snatch": {"reps": 3, "notes": "Build to heavy 1-rep power snatch"},
                    "Overhead Squat": {"reps": 2, "notes": "After each successful snatch"}
                },
                "notes": ["Focus on bar path", "Maintain active shoulders"]
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Deadlift", "Power Clean", "Front Squat"],
        "training_program": {
            "10 rounds for time": {
                "round_target": {
                    "Deadlift": {"reps": 4, "weight": "45/60kg"},
                    "Power Clean": {"reps": 3},
                    "Front Squat": {"reps": 2}
                },
                "notes": ["Maintain form throughout", "Touch and go on deadlifts allowed"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },
    {
        "exercises_used": ["Running", "Bear Crawl", "Samson Lunges", "Spiderman Stretch", "Inchworm", "Crab Walk",
                           "Burpee", "High Knee", "Butt Kicker"],
        "training_program": {
            "circuit": {
                "round_target": {
                    "Running 1": {"distance": "200m", "notes": "moderate pace"},
                    "Bear Crawl": {"distance": "7.5M"},
                    "Samson Lunges": {"distance": "7.5M"},
                    "Spiderman Stretch": {"distance": "7.5M"},
                    "Inchworm": {"distance": "7.5M", "notes": "with push-up"},
                    "Crab Walk": {"distance": "7.5M", "notes": "high hips"},
                    "High Knee": {"distance": "7.5M"},
                    "Butt Kicker": {"distance": "7.5M"},
                    "Running 2": {"distance": "200m", "notes": "fast/stride"}
                },
                "notes": ["Focus on quality movement", "Maintain proper form throughout"]
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Handstand Push-up", "Push Press"],
        "training_program": {
            "skill work": {
                "round_target": {
                    "Handstand Push-up": {"reps": "5-8", "notes": "practice holds if needed"},
                    "Push Press": {"reps": "8", "notes": "build to working weight"}
                },
                "notes": ["Focus on balance and control", "Practice wall walks if needed"]
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Deadlift", "Hang Power Clean", "Front Squat"],
        "training_program": {
            "12 rounds for time": {
                "round_target": {
                    "Deadlift": {"reps": 4, "weight": "45/60kg"},
                    "Hang Power Clean": {"reps": 3},
                    "Front Squat": {"reps": 2}
                },
                "notes": ["Touch and go allowed", "Maintain full front rack in squats"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },
    {
        "exercises_used": ["Row", "Single Under", "Toy Soldier", "Push-up"],
        "training_program": {
            "3 rounds": {
                "round_target": {
                    "Row": {"calories": 10},
                    "Single Under": {"reps": 50},
                    "Toy Soldier": {"reps": 10},
                    "Push-up": {"reps": 10}
                },
                "rest": "30 sec between rounds",
                "notes": ["Focus on proper jumping mechanics", "Scale push-ups as needed"]
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Back Squat"],
        "training_program": {
            "Every 3min x 5 sets": {
                "round_target": {
                    "Back Squat": {"scheme": "10-8-8-6-6", "notes": "Build in weight each set"}
                },
                "notes": ["Start light and build to @8 RPE", "Focus on form and depth"]
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Air Squat", "Push-up", "Pull-up"],
        "training_program": {
            "AMRAP 20": {
                "round_target": {
                    "Air Squat": {"reps": 15},
                    "Push-up": {"reps": 10},
                    "Pull-up": {"reps": 5}
                },
                "notes": ["Known as 'Cindy'", "Scale movements as needed", "Maintain consistent pace"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },
    {
        "exercises_used": ["Running", "Jumping Jacks", "Push-up", "Spiderman Lunge", "Burpee", "Scorpion Stretch"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "Running": {"distance": "400m", "notes": "jog"},
                    "Jumping Jacks": {"reps": 20},
                    "Push-up": {"reps": 10, "notes": "to down-dog"},
                    "Spiderman Lunge": {"reps": 10, "notes": "alternating"},
                    "Burpee": {"reps": 10},
                    "Scorpion Stretch": {"reps": 10, "notes": "alternating"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Bench Press"],
        "training_program": {
            "Build up": {
                "round_target": {
                    "Bench Press": {"notes": "15:00 To build to 1RM"}
                },
                "notes": ["Focus on proper setup", "Use spotters when needed"]
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Hand Release Push-up", "Running"],
        "training_program": {
            "For Time": {
                "round_target": {
                    "Hand Release Push-up": {"reps": "9-15-21-9"},
                    "Running": {"distance": ["100m", "200m", "300m", "400m"]}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # שני 11
    {
        "exercises_used": ["PVC Pass Through", "Spiderman Stretch", "Push-up", "Scap Pull-up",
                           "Dumbbell Shoulder Press"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "PVC Pass Through": {"reps": 10},
                    "Spiderman Stretch": {"reps": 10, "notes": "alternating"},
                    "Push-up": {"reps": 5},
                    "Scap Pull-up": {"reps": 5},
                    "Dumbbell Shoulder Press": {"reps": "5/arm"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Dumbbell Thruster"],
        "training_program": {
            "Last prep": {
                "round_target": {
                    "Dumbbell Thruster": {
                        "reps": 10,
                        "notes": "unbroken at workout weight"
                    }
                }
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Dumbbell Thruster", "Pull-up"],
        "training_program": {
            "For Time": {
                "round_target": {
                    "Dumbbell Thruster": {"reps": "27-21-15-9", "weight": "10/15 kg"},
                    "Pull-up": {"reps": "27-21-15-9"}
                },
                "notes": ["Use two DBs"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # שלישי 12
    {
        "exercises_used": ["AbMat Sit-up", "Row", "Assault Bike"],
        "training_program": {
            "In team of 2": {
                "round_target": {
                    "AbMat Sit-up": {"reps": 20, "weight": "20/14 lbs medball"},
                    "Row": {"calories": "16/12"},
                    "Assault Bike": {"calories": "12/10"}
                },
                "notes": ["Partners split work as needed"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 15
    },

    # רביעי 13
    {
        "exercises_used": ["Spiderman Stretch", "Scorpion Stretch", "Deadlift", "Shoulder Press", "Jumping Jack"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "Spiderman Stretch": {"reps": 10},
                    "Scorpion Stretch": {"reps": 10},
                    "Deadlift": {"reps": 10, "notes": "empty grip"},
                    "Shoulder Press": {"reps": 10},
                    "Jumping Jack": {"reps": 30}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Clean and Jerk"],
        "training_program": {
            "Every minute for 5 minutes": {
                "round_target": {
                    "Clean and Jerk": {"reps": 3, "notes": "touch and go"}
                },
                "notes": ["Increase load each minute", "Rest 1 minute between sets"]
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },

    # חמישי 14
    {
        "exercises_used": ["Mountain Climber", "Burpee", "Air Squat"],
        "training_program": {
            "PVC SWITCH WARM-UP": {
                "Penalty movements": {
                    "Mountain Climber": {"reps": 20},
                    "Burpee": {"reps": 5},
                    "Air Squat": {"reps": 10}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["KB Swing", "Shuttle Run"],
        "training_program": {
            "2 rounds for time": {
                "round_target": {
                    "KB Swing": {"reps": 50, "weight": "32/24 kg"},
                    "Shuttle Run": {"reps": 50}
                },
                "notes": ["One partner works at a time", "Switch as needed"],
                "rest": "1 shuttle run = 7.5M down/7.5M back"
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # שישי 15
    {
        "exercises_used": ["Jump Rope", "Calf Raise", "Plank Shoulder Tap", "Mountain Climber", "Single Unders",
                           "Inchworm"],
        "training_program": {
            "3 sets": {
                "round_target": {
                    "Jump Rope": {"reps": 20},
                    "Calf Raise": {"reps": 10},
                    "Plank Shoulder Tap": {"reps": 20},
                    "Mountain Climber": {"reps": 20},
                    "Single Unders": {"reps": 20},
                    "Inchworm": {"reps": 5, "notes": "with push-ups"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Power Clean"],
        "training_program": {
            "skill progression": {
                "round_target": {
                    "Power Clean 1": {"reps": "20 jump rope/DU or single unders"},
                    "Power Clean 2": {"reps": 2, "notes": "build technique"}
                },
                "rest": "1:00 between sets"
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Double Under", "Push-up", "Power Clean"],
        "training_program": {
            "AMRAP 25": {
                "round_target": {
                    "Double Under": {"reps": 150},
                    "Push-up": {"reps": 50},
                    "Power Clean": {"reps": 15, "weight": "35/52.5kg"}
                },
                "notes": ["Partners split work as desired"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 25
    },
    {
        "exercises_used": ["Jumping Jack", "Inchworm", "Samson Stretch", "Ring Row"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "Jumping Jack": {"reps": 20},
                    "Inchworm": {"reps": 5},
                    "Samson Stretch": {"reps": 10},
                    "Ring Row": {"reps": 10},
                },
                "notes": ["Walk the feet forward to increase the difficulty of the row"]
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Bench Press"],
        "training_program": {
            "For load": {
                "round_target": {
                    "Bench Press": {"scheme": "5-5-5-5-5"},
                    "notes": ["Max reps on the last set",
                              "Use the same load for sets 4 and 5, but go for more than 5 reps in that final set",
                              "Use a spotter if possible"]
                }
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Pull-up", "Push-up", "Air Squat"],
        "training_program": {
            "Cindy": {
                "AMRAP 20": {
                    "round_target": {
                        "Pull-up": {"reps": 5},
                        "Push-up": {"reps": 10},
                        "Air Squat": {"reps": 15}
                    },
                    "notes": ["Scale movements as needed", "Maintain consistent pace"]
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # שני 4
    {
        "exercises_used": ["Running", "Spiderman Stretch", "Plank Reach Through", "V-ups", "Bear Crawl",
                           "Scap Pull-up"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "Running": {"distance": "200m"},
                    "Spiderman Stretch": {"reps": 10, "notes": "alternating"},
                    "Plank Reach Through": {"reps": 10, "notes": "alternating"},
                    "V-ups": {"reps": 10, "notes": "alternating single-leg"},
                    "Bear Crawl": {"reps": 10},
                    "Scap Pull-up": {"reps": 10}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Push Press"],
        "training_program": {
            "On a 10:00 clock": {
                "round_target": {
                    "Push Press": {
                        "reps": 5,
                        "notes": ["Build to a heavy set of 5 reps", "From the floor"]
                    }
                }
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Sumo Deadlift High Pull", "Push Press", "Box Jump Over"],
        "training_program": {
            "7 rounds for time": {
                "round_target": {
                    "Sumo Deadlift High Pull": {"reps": 7, "weight": "42.5/30kg"},
                    "Push Press": {"reps": 7},
                    "Box Jump Over": {"reps": 7, "height": "#70/#50 CM"}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },
    {
        "exercises_used": ["Row", "Assault Bike", "Devil Press"],
        "training_program": {
            "4 Rounds": {
                "round_target": {
                    "Row/Assault Bike": {"calories": "100/80"},
                    "Devil Press": {"reps": 14, "weight": "22.5/15 kg"}
                },
                "rest": "2:00 between rounds",
                "notes": ["Cap machine at 4:00", "Partners switch on machines as needed"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 33
    },

    # רביעי 6
    {
        "exercises_used": ["Jumping Jack", "Good Morning", "Box Step Over", "Box Jump Over"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "Jumping Jack": {"reps": 20},
                    "Good Morning": {"reps": 10, "notes": "wide stance"},
                    "Box Step Over": {"reps": 5},
                    "Box Jump Over": {"reps": 5}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Wall Walk", "Toes to Bar"],
        "training_program": {
            "AMRAP 10": {
                "round_target": {
                    "Wall Walk": {"reps": 2},
                    "Toes to Bar": {"reps": 3}
                },
                "notes": ["Scale as needed", "Focus on quality movement"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 15
    },

    # חמישי 7
    {
        "exercises_used": ["Single Under", "Back Rack Position", "Deadlift", "Hang Power Clean", "Front Squat"],
        "training_program": {
            "Complex": {
                "Lifting Complex": {
                    "3 sets": {
                        "Deadlift": {"reps": 3},
                        "Hang Power Clean": {"reps": 3},
                        "Front Squat": {"reps": 3}
                    },
                    "notes": ["Build to workout weight"]
                }
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Deadlift", "Hang Power Clean", "Front Squat"],
        "training_program": {
            "For Time": {
                "round_target": {
                    "Deadlift": {"reps": "7-7-5", "weight": "52.5/35 kg"},
                    "Hang Power Clean": {"reps": "prescribed"},
                    "Front Squat": {"reps": "prescribed"}
                },
                "time_cap": "8:00"
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 8
    },

    # שבת 9
    {
        "exercises_used": ["Running", "Single Under", "Samson Stretch", "Burpee", "Dumbbell Shoulder Press"],
        "training_program": {
            "warm-up": {
                "round_target": {
                    "Running": {"distance": "400m", "notes": "jog"},
                    "Single Under": {"reps": 50},
                    "Samson Stretch": {"reps": 10, "notes": "per leg"},
                    "Burpee": {"reps": 10},
                    "Dumbbell Shoulder Press": {"reps": "5 each arm"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Double Under", "Burpee", "Dumbbell Snatch", "Overhead Lunge", "Row", "Assault Bike"],
        "training_program": {
            "For Time": {
                "round_target": {
                    "Double Under": {"reps": 200},
                    "Burpee": {"reps": 40},
                    "Dumbbell Snatch": {"reps": "40 each arm", "weight": "22.5/15"},
                    "Overhead DB Lunge": {"reps": 100, "notes": "single-arm"},
                    "Row/Assault Bike": {"distance/calories": "800/1000m or 2500/2000M"}
                },
                "notes": ["Use one dumbbell", "Switch arms on lunges as needed"],
                "time_cap": "34:00"
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 34
    },
    {
        "exercises_used": ["Up Down", "Scorpion Stretch", "Single Leg Toe Touch", "Air Squat", "Burpee",
                           "Samson Stretch", "Good Morning", "Mountain Climber"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "Up Down": {"reps": 30},
                    "Scorpion Stretch": {"reps": 10, "notes": "alternating"},
                    "Single Leg Toe Touch": {"reps": 10},
                    "Air Squat": {"reps": 10},
                    "Burpee": {"reps": 50},
                    "Samson Stretch": {"reps": 10},
                    "Good Morning": {"reps": 10, "notes": "unweighted"},
                    "Mountain Climber": {"reps": 20}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Toes To Bar"],
        "training_program": {
            "EMOM 7": {
                "round_target": {
                    "Toes To Bar": {"reps": "6-10"}
                }
            }
        },
        "training_type": "skill",
        "training_source": "rocklee",
        "training_time": 7
    },
    {
        "exercises_used": ["Rope Climb", "Devil Press"],
        "training_program": {
            "EMOM 12": {
                "round_target": {
                    "odd_minutes": {"Legless Rope Climb": {"reps": 2}},
                    "even_minutes": {"Devil Press": {"reps": "Max-reps", "weight": "15/10 kg"}}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 12
    },

    # שני 28
    {
        "exercises_used": ["Running", "Bear Crawl", "Samson Lunge", "Spiderman Twist", "Crab Walk", "Burpee"],
        "training_program": {
            "circuit": {
                "round_target": {
                    "Running 1": {"distance": "400m", "notes": "easy pace"},
                    "Bear Crawl": {"distance": "7.5 M down"},
                    "Samson Lunge": {"distance": "7.5 M back"},
                    "Spiderman Twist": {"distance": "7.5 M"},
                    "Crab Walk": {"notes": "focus on maintaining high hips"},
                    "Burpee Broad Jump": {"distance": "7.5 M"},
                    "Running 2": {"distance": "200m", "notes": "moderate pace"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Dumbbell Front Rack", "Front Rack Lunge"],
        "training_program": {
            "For Time": {
                "round_target": {
                    "Dumbbell Front Rack": {"reps": "1-1-1", "notes": "min"},
                    "Front Rack Lunge": {"distance": "36m"}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # שלישי 29
    {
        "exercises_used": ["Single Under", "Scorpion Stretch", "Push-up"],
        "training_program": {
            "3 sets": {
                "round_target": {
                    "Single Under": {"reps": 40},
                    "Scorpion Stretch": {"reps": 10, "notes": "alternating"},
                    "Push-up": {"reps": "5-10", "notes": "tempo 5/5"}
                },
                "notes": ["Every round go for next option"]
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Skin the Cat"],
        "training_program": {
            "skill work": {
                "round_target": {
                    "Skin the Cat": {"reps": 20, "notes": "practice any variation"}
                }
            }
        },
        "training_type": "skill",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Row", "Push-up"],
        "training_program": {
            "5 rounds": {
                "round_target": {
                    "Row": {"notes": "@8 Rpe"},
                    "Push-up": {"reps": 30}
                },
                "notes": ["Score is total calories and push-up reps"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # רביעי 30
    {
        "exercises_used": ["Step Up", "Calf Raise", "Jump Rope", "Samson Stretch", "Single DB Press", "Goblet Squat"],
        "training_program": {
            "1 set": {
                "round_target": {
                    "Step Up": {"reps": 10, "notes": "alternating"},
                    "Calf Raise": {"reps": 10, "notes": "slow"},
                    "Jump Rope": {"time": "1:00", "notes": "practice"},
                    "Samson Stretch": {"reps": 10},
                    "Single DB Press": {"reps": "5/arm"},
                    "Goblet Squat": {"reps": 20}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Turkish Get Up"],
        "training_program": {
            "4 sets": {
                "round_target": {
                    "Turkish Get Up": {"reps": "4/side", "notes": "alternating"},
                },
                "rest": "1:00 between sets",
                "notes": ["Use a single dumbbell"]
            }
        },
        "training_type": "skill",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Box Step Up", "Double Under"],
        "training_program": {
            "For Time": {
                "round_target": {
                    "Box Step Up": {"reps": 50, "height": "60/50cm"},
                    "Double Under": {"reps": 50}
                },
                "notes": ["Every minute on the minute, starting at 0:00", "Use two dumbbells"],
                "time_cap": "20:00"
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # חמישי 31
    {
        "exercises_used": ["Running", "PVC Pass Through", "Good Morning", "Muscle Clean", "Front Squat", "Push-up"],
        "training_program": {
            "3 rounds": {
                "round_target": {
                    "Running": {"distance": "400m", "notes": "jog"},
                    "PVC Pass Through": {"reps": 10},
                    "Good Morning": {"reps": 10},
                    "Muscle Clean": {"reps": 10},
                    "Front Squat": {"reps": 10},
                    "Push-up": {"reps": 10}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Low Bar Muscle Up", "Hang Squat Clean"],
        "training_program": {
            "3-4 sets": {
                "round_target": {
                    "Hang Squat Clean": {"notes": "Build to workout load"},
                    "Bar Muscle Up": {"reps": 2}
                },
                "rest": "1:00 between sets",
                "notes": ["Or movement variation for the workout"]
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Hang Squat Clean", "Bar Muscle Up"],
        "training_program": {
            "5 rounds for time": {
                "round_target": {
                    "Hang Squat Clean": {"reps": 7, "weight": "70/50kg"},
                    "Bar Muscle Up": {"reps": 5}
                },
                "notes": ["Scale movements as needed"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # שבת 2
    {
        "exercises_used": ["Running", "DB Deadlift", "DB Press", "Plank"],
        "training_program": {
            "2 rounds": {
                "round_target": {
                    "Running": {"distance": "200m"},
                    "Single DB Deadlift": {"reps": 10},
                    "Single DB Press": {"reps": "5/arm"},
                    "Plank Hold": {"time": "30 sec"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Row", "Assault Bike", "DB Bench Press", "T2B", "DB"],
        "training_program": {
            "In teams of 2": {
                "For time": {
                    "round_target": {
                        "Row/Assault Bike 1": {"calories": "50/40"},
                        "DB Bench Press": {"reps": 50, "weight": "22.5/15"},
                        "T2B": {"reps": 40},
                        "Row/Assault Bike 2": {"calories": "50/40"}
                    },
                    "notes": ["I go you go", "Switch however you prefer",
                              "Scale load accordingly for at least 50 DB Bench press"],
                    "time_cap": "30:00"
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 30
    },
    {
        "exercises_used": ["Running", "Single Under", "Spiderman Stretch", "Push-up", "Box Step-up"],
        "training_program": {
            "1 round": {
                "round_target": {
                    "Running": {"distance": "200m", "notes": "jog"},
                    "Single Under": {"reps": 20},
                    "Spiderman Stretch": {"reps": 10, "notes": "alternating"},
                    "Push-up": {"reps": 5, "notes": "to downward dog"},
                    "Box Step-up": {"reps": 10}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Dumbbell Farmers Carry", "Front Rack Hold"],
        "training_program": {
            "4 sets for load": {
                "round_target": {
                    "Dumbbell Farmers Carry": {"distance": "100m"},
                    "Front Rack Hold": {"time": "1:00", "notes": "dual DB"}
                },
                "notes": [
                    "Use two dumbbells/KBs for the farmers carry",
                    "Relatively heavy grunt work",
                    "Build in load to a heavy set",
                    "Rest 10-20 seconds between movements"
                ]
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Box Jump Over", "Push-up", "Pull-up"],
        "training_program": {
            "For time": {
                "round_target": {
                    "Box Jump Over": {"reps": 20, "height": "60/50 CM"},
                    "Push-up": {"reps": 20},
                    "Pull-up": {"reps": 20}
                },
                "time_cap": "15:00"
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 15
    },

    # שני 21
    {
        "exercises_used": ["Medicine Ball Pass", "Medicine Ball Side Pass", "Medicine Ball Clean"],
        "training_program": {
            "2 sets with a partner": {
                "round_target": {
                    "Medicine Ball Chest Pass": {"reps": 30},
                    "Medicine Ball Side Pass": {"reps": 30, "notes": "each side"},
                    "Medicine Ball Clean": {"reps": 30}
                },
                "rest": "30 between sets",
                "notes": ["Focus on power clean progression"]
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Power Clean"],
        "training_program": {
            "For load": {
                "scheme": "3-3-3-3-3",
                "notes": ["Build for heavy triple for the day", "14:00 cap"]
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 14
    },
    {
        "exercises_used": ["Run", "Burpee Over Bar", "Power Clean"],
        "training_program": {
            "17:00 AMRAP": {
                "round_target": {
                    "Run": {"distance": "400 M"},
                    "Burpee Over Bar": {"reps": 4},
                    "Power Clean": {"reps": 7, "notes": "75%"}
                },
                "notes": ["Use 75% of your heaviest set of the day"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 17
    },

    # שלישי 22
    {
        "exercises_used": ["Ring Row", "Knee Push-up", "Air Squat", "Scap Pull-up", "Push-up",
                           "Medicine Ball Front Squat"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "Ring Row": {"reps": 10},
                    "Knee Push-up": {"reps": 10},
                    "Air Squat": {"reps": 10},
                    "Scap Pull-up": {"reps": 5},
                    "Push-up": {"reps": 5},
                    "Medicine Ball Front Squat": {"reps": 5, "notes": "hold bottom for 3s"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Strict Muscle Up"],
        "training_program": {
            "skill progression": {
                "round_target": {
                    "Strict Muscle Up": {
                        "time": "13:00-15:00",
                        "notes": ["Practice ring transitions", "Scale to appropriate progression"]
                    }
                }
            }
        },
        "training_type": "skill",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Wall Ball", "Strict Muscle Up"],
        "training_program": {
            "For time": {
                "round_target": {
                    "Wall Ball": {"scheme": "50-40-30", "weight": "14/20 lb"},
                    "Strict Muscle Up": {"scheme": "4-4-3"}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # רביעי 23
    {
        "exercises_used": ["Deadlift"],
        "training_program": {
            "Build up": {
                "3 sets": {
                    "Deadlift": {"notes": "Build in load to workout weight"}
                },
                "time": "6:00-7:00"
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Double Under", "Deadlift"],
        "training_program": {
            "7 x 1:00 rounds of": {
                "round_target": {
                    "Double Under": {"reps": 21},
                    "Deadlift": {"reps": "max reps", "weight": "140/100 kg"}
                },
                "rest": "2:00 between rounds"
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # חמישי 24
    {
        "exercises_used": ["Running", "Kettlebell Deadlift", "Burpee", "Kettlebell Swing", "Row", "Bike"],
        "training_program": {
            "circuit": {
                "round_target": {
                    "Running": {"distance": "200m", "notes": "slow"},
                    "Kettlebell Deadlift": {"reps": 10},
                    "Burpee": {"reps": 5, "notes": "Perfect"},
                    "Kettlebell Swing": {"reps": 10},
                    "Row/Bike": {"calories": 7},
                    "Running": {"distance": "200m", "notes": "fast"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Toes to Bar", "Kettlebell Swing", "Double Under"],
        "training_program": {
            "3:00 Sets for time": {
                "round_target": {
                    "Toes to Bar": {"time": "3:00"},
                    "Kettlebell Swing": {"time": "3:00", "weight": "24/16"},
                    "Machine": {"calories": "3:00"},
                    "Double Under": {"notes": "run 200m at the start of each interval"}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # שבת 25
    {
        "exercises_used": ["Running", "DB Deadlift", "DB Press", "Handstand Push-up", "Farmers Carry"],
        "training_program": {
            "2 rounds": {
                "round_target": {
                    "Running": {"distance": "200m"},
                    "Single DB Deadlift": {"reps": 10},
                    "Single DB Press": {"reps": "5/arm"},
                    "Handstand Push-up": {"reps": 5},
                    "Farmers Carry": {"distance": "30m", "notes": "out and back"}
                },
                "notes": ["Use workout variations and loads", "Split the work evenly and practice fast transitions"]
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Alt DB Hang Squat Snatch", "Handstand Push-up", "DB Farmers Carry"],
        "training_program": {
            "AMRAP 14 with a partner": {
                "round_target": {
                    "Alt DB Hang Squat Snatch": {"reps": 24, "weight": "24/16"},
                    "Handstand Push-up": {"reps": 12},
                    "DB Farmers Carry": {"distance": "200m"}
                },
                "notes": ["Share work load as desired", "Use two KBs for the farmers carry"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 14
    },
    {
        "exercises_used": ["Jog", "Karaoke", "Knee to Chest", "Twist", "High Knees", "Butt Kicks"],
        "training_program": {
            "1 round": {
                "round_target": {
                    "each drill": {"distance": "7.5 M down and back"},
                    "notes": ["High knee karaoke", "Knee to chest", "Lunge with a torso twist", "High knees",
                              "Butt kicks"]
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Single Leg Squat"],
        "training_program": {
            "MINI ROUND": {
                "2 rounds for time with a partner": {
                    "Running": {"distance": "100m"},
                    "Single Leg Squat": {"reps": 12, "notes": "alternating"},
                    "notes": ["Run together and perform 6 single-leg squats each"]
                }
            }
        },
        "training_type": "skill",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Single Leg Squat"],
        "training_program": {
            "5 rounds for time with a partner": {
                "round_target": {
                    "Single Leg Squat": {"reps": 40, "notes": "alternating"},
                    "Running": {"distance": "200m"}
                },
                "notes": ["Run together and break up the squats as needed"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # שני 14
    {
        "exercises_used": ["Samson Stretch", "PVC Overhead Squat", "Good Morning", "Hollow Rock", "Push-up", "Ring Row",
                           "Strict Pull-up"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "Samson Stretch": {"reps": 10},
                    "PVC Overhead Squat": {"reps": 10},
                    "Good Morning": {"reps": 10},
                    "Hollow Rock": {"reps": 10},
                    "Push-up": {"reps": 10},
                    "Ring Row OR Strict Pull-up": {"reps": "3-10"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Kettlebell Front Rack Carry"],
        "training_program": {
            "10 rounds for load": {
                "round_target": {
                    "KB Front Rack Carry": {"distance": "50m", "notes": "Dual KB"}
                },
                "rest": "1:00 between rounds",
                "notes": [
                    "Finish each carry in less than 1:00",
                    "Record the heaviest successful carry",
                    "Build up to the heaviest KBs or objects"
                ]
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 20
    },
    {
        "exercises_used": ["Box Jump", "Wall Walk"],
        "training_program": {
            "3 rounds for time with a partner": {
                "round_target": {
                    "Box Jump": {"reps": 40},
                    "Wall Walk": {"reps": 12}
                },
                "notes": ["One athlete works at a time. Athletes may alternate as they see fit."]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # שלישי 15
    {
        "exercises_used": ["Running", "Elbow to Instep", "Mountain Climber", "Prisoner Squat", "Burpee"],
        "training_program": {
            "2 rounds": {
                "round_target": {
                    "Running": {"distance": "400m"},
                    "Elbow to Instep": {"reps": "5/side"},
                    "Mountain Climber": {"reps": 20},
                    "Prisoner Squat": {"reps": 10},
                    "Burpee": {"reps": 5}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Front Squat"],
        "training_program": {
            "Every 1:30 x 7 sets": {
                "round_target": {
                    "Front Squat": {"scheme": "1-1-1-1-1-1-1"}
                },
                "notes": ["The final set should be the heaviest", "Find a heavy single front squat for the day"]
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Running", "KB Swing", "Single KB Farmers Carry"],
        "training_program": {
            "AMRAP 20": {
                "round_target": {
                    "Running": {"distance": "400m"},
                    "KB Swing": {"reps": 32, "weight": "32/24"},
                    "Single KB Farmers Carry": {"distance": "400m"}
                },
                "notes": ["Partners run together and break up the other two movements as needed."]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # רביעי 16
    {
        "exercises_used": ["Shuttle Run", "Step Up", "Box Step Up", "Dumbbell Box Step Up"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "Shuttle Run": {"notes": "easy pace"},
                    "Step Up": {"reps": 10},
                    "Jump Air Squat": {"reps": 5},
                    "Dumbbell Box Step Up": {"reps": 10}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Power Snatch", "Machine", "Box Step Up"],
        "training_program": {
            "For reps": {
                "4 rounds": {
                    "Power Snatch": {"reps": 1, "weight": "workout weight"},
                    "Machine": {"calories": 20},
                    "Box Step Up": {"reps": 20}
                },
                "rest": "1:00 between movements"
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # חמישי 17
    {
        "exercises_used": ["Jumping Jack", "Air Squat", "Push-up", "Box Jump Over", "Wall Ball", "Burpee"],
        "training_program": {
            "2 set": {
                "round_target": {
                    "Jumping Jack": {"reps": 10},
                    "Air Squat": {"reps": 10},
                    "Push-up": {"reps": 10},
                    "Box Jump Over": {"reps": 10},
                    "Wall Ball Push Press": {"reps": 10},
                    "Burpee": {"reps": 5}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Plank Hold", "Toes to Bar", "Strict Toes to Bar"],
        "training_program": {
            "For time": {
                "round_target": {
                    "Plank Hold 1": {"time": "1:00", "notes": "straight arms"},
                    "Toes to Bar": {"reps": 25},
                    "Plank Hold 2": {"time": "1:00", "notes": "on forearms"},
                    "Strict Toes to Bar": {"reps": 25}
                },
                "time_cap": "15:00",
                "notes": ["No more than 2 sets on plank holds"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 15
    },

    # שבת 18
    {
        "exercises_used": ["Spiderman Stretch", "Leg Swing", "Scorpion Stretch", "Jumping Jack", "Deadlift",
                           "Shoulder Press", "Up Down"],
        "training_program": {
            "1 set": {
                "round_target": {
                    "Spiderman Stretch": {"reps": 10, "notes": "alternating"},
                    "Leg Swing 1": {"reps": "10/leg", "notes": "across the body"},
                    "Scorpion Stretch": {"reps": 10, "notes": "alternating"},
                    "Leg Swing 2": {"reps": "10/leg", "notes": "forward and backward"},
                    "Jumping Jack": {"reps": 30},
                    "Deadlift": {"reps": 10, "notes": "empty barbell"},
                    "Shoulder Press": {"reps": 10, "notes": "empty barbell"},
                    "Up Down": {"reps": 30}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Power Clean", "Burpee", "Box Jump Over"],
        "training_program": {
            "with a partner": {
                "Every 2:30 for 15:00 (6 sets)": {
                    "Power Clean": {"reps": 3, "weight": "60/40 kg"},
                    "Burpee Over Bar": {"reps": 3},
                    "Box Jump Over": {"reps": 3, "height": "60/50 CM"}
                },
                "rest": "30 sec each round",
                "notes": [
                    "This is six, all out sprints intended to be completed unbroken",
                    "Rx rx for today- power clean must be unbroken- cap is 60/40 kg"
                ]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Running", "Spiderman Stretch", "Samson Stretch", "Leg Swing", "Handstand Hold"],
        "training_program": {
            "1 set": {
                "round_target": {
                    "Running": {"distance": "200m", "notes": "jog"},
                    "Spiderman Stretch": {"reps": 10, "notes": "alternating"},
                    "Samson Stretch": {"time": "30/20 sec"},
                    "Leg Swing": {"reps": 10, "notes": "forward and backward"},
                    "Handstand Hold": {"time": "30 sec"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Single Leg Toe Touch", "Reverse Lunge", "Band Pull Apart", "Handstand Hold"],
        "training_program": {
            "1 set": {
                "round_target": {
                    "Single Leg Toe Touch": {"reps": 10},
                    "Reverse Lunge": {"reps": 10, "notes": "alternating"},
                    "Band Pull Apart": {"reps": 10},
                    "Handstand/Plank Hold": {"time": "30 sec"}
                }
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Walking Lunge", "Push-up", "KB Strict Press"],
        "training_program": {
            "AMRAP 10": {
                "round_target": {
                    "Walking Lunge": {"reps": 30},
                    "Push-up": {"reps": 4},
                    "KB Strict Press": {"reps": "4/arm", "weight": "16/12 kg"}
                },
                "notes": ["Scale movements as needed"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 10
    },

    # שני 7
    {
        "exercises_used": ["Running", "Inchworm", "Air Squat", "DB Snatch", "Kip Swing"],
        "training_program": {
            "2 rounds": {
                "round_target": {
                    "Running": {"distance": "200m"},
                    "Inchworm": {"reps": 5, "notes": "with push up"},
                    "Air Squat": {"reps": 10},
                    "DB Snatch": {"reps": 10},
                    "Kip Swing": {"reps": 10}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Power Clean", "Front Squat", "Shoulder To Overhead", "Bar Muscle Up"],
        "training_program": {
            "OCTOBER 7th - CFSR Hero WOD": {
                "7 Rounds For Time": {
                    "Power Clean": {"reps": 10},
                    "Front Squat": {"reps": 10},
                    "Shoulder To Overhead": {"reps": 10},
                    "Bar Muscle Up": {"reps": 10}
                },
                "notes": ["With a Partner", "Cap 25min", "Rx 70/45", "Partition the reps with the partner as needed"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 25
    },

    # שלישי 8
    {
        "exercises_used": ["Single Under", "Samson Lunge", "Single Leg V-up", "Hollow Hold", "Scap Pull Up"],
        "training_program": {
            "3 rounds": {
                "round_target": {
                    "Single Under": {"reps": 30},
                    "Samson Lunge": {"reps": 30},
                    "Single Leg V-up": {"reps": 10, "notes": "alternating"},
                    "Hollow Hold": {"time": "30 sec"},
                    "Scap Pull Up": {"reps": 10}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Strict Press"],
        "training_program": {
            "Build up": {
                "notes": ["16:00 To build for 1RM For today"]
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 16
    },
    {
        "exercises_used": ["Kettlebell Swing", "Toes to Bar"],
        "training_program": {
            "For time": {
                "round_target": {
                    "Kettlebell Swing": {"scheme": "21-15-12-9-6-3", "weight": "32/24"},
                    "Toes to Bar": {"scheme": "3-6-9-12-15-18"}
                },
                "notes": ["Scale as needed"]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # רביעי 9
    {
        "exercises_used": ["PVC Pass Through", "Good Morning", "Front Squat", "Plank Hold"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "PVC Pass Through": {"reps": 10},
                    "PVC Good Morning": {"reps": 10},
                    "PVC Front Squat": {"reps": 10},
                    "Side Plank Hold": {"time": "15 sec", "notes": "per side"},
                    "Plank Hold": {"time": "20 sec"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Power Clean"],
        "training_program": {
            "Build up": {
                "2-3 sets": {
                    "Power Clean": {"reps": 3, "notes": "building"}
                },
                "warm up round": {
                    "Plank Hold": {"time": "30 sec"},
                    "Power Clean": {"reps": 1, "notes": "unbroken"}
                }
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Power Clean", "Running", "Plank Hold"],
        "training_program": {
            "3 rounds for time": {
                "round_target": {
                    "Power Clean": {"reps": 21, "weight": "70/50 kg"},
                    "Running": {"distance": "200m"},
                    "Plank Hold": {"notes": "time equal to run time, should be unbroken"}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # חמישי 10
    {
        "exercises_used": ["Running", "Single Under", "Samson Stretch", "Leg Press", "Morning"],
        "training_program": {
            "2 sets": {
                "round_target": {
                    "Running": {"distance": "200M", "notes": "jog"},
                    "Single Under": {"reps": 30},
                    "Samson Stretch": {"reps": "20/leg"},
                    "Single Leg Press": {"reps": "5/5", "notes": "good morning-slow and controlled"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Deadlift"],
        "training_program": {
            "strength": {
                "notes": ["20:00 to build up for 1RM"]
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 20
    },
    {
        "exercises_used": ["Machine", "KB Swing"],
        "training_program": {
            "in team of 2": {
                "For time": {
                    "Machine": {"calories": "42-30-18 M/36-24-14 W"},
                    "KB Swing": {"reps": "36/24", "weight": "24/16 Or 22.5/15 Kg DBS"}
                },
                "notes": [
                    "the calories are meant to be completed as fast as possible",
                    "I go you go for the Machines and dual swing-split it as you prefer to go as fast as possible",
                    "Target time-7:00-10:00"
                ]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    },

    # שבת 11
    {
        "exercises_used": ["Air Squat", "Granny Toss", "Chest Pass", "Side Toss", "Roll Pass", "Squat Toss"],
        "training_program": {
            "1 round": {
                "round_target": {
                    "Air Squat": {"reps": 10, "notes": "no ball"},
                    "Granny Toss": {"reps": 10},
                    "Chest Pass": {"reps": 10},
                    "Side Toss": {"reps": "10/side"},
                    "Roll Pass": {"reps": 10},
                    "Squat Toss": {"reps": 10}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Bar Muscle Up"],
        "training_program": {
            "skill progression": {
                "notes": ["Bar Muscle Up practice"]
            }
        },
        "training_type": "skill",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Wall Ball", "Bar Muscle Up", "Wall Walk"],
        "training_program": {
            "AMRAP 25 with a partner": {
                "round_target": {
                    "Wall Ball": {"reps": 20, "weight": "14/20 lb"},
                    "Bar Muscle Up": {"reps": 10},
                    "Wall Walk": {"reps": 5}
                },
                "notes": ["Partners split work as needed."]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 25
    },
    {
        "exercises_used": ["Row", "Plank", "Kip Swing", "Samson Stretch"],
        "training_program": {
            "AMRAP 5": {
                "round_target": {
                    "Row/Single Under/Shuttle Run": {"distance": "30m"},
                    "Plank Reach Through": {"reps": 10, "notes": "alternating"},
                    "Kip Swing": {"reps": 10},
                    "Samson Stretch": {"reps": "30/side"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Pull-up", "Push-up", "Sit-up", "Air Squat"],
        "training_program": {
            "2 rounds": {
                "round_target": {
                    "Pull-up": {"reps": 3},
                    "Push-up": {"reps": 5},
                    "Sit-up": {"reps": 3},
                    "Air Squat": {"reps": 3}
                }
            }
        },
        "training_type": "skill",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Pull-up", "Push-up", "Sit-up", "Squat"],
        "training_program": {
            "5 rounds, each for time": {
                "round_target": {
                    "Pull-up": {"reps": 20},
                    "Push-up": {"reps": 30},
                    "Sit-up": {"reps": 40},
                    "Squat": {"reps": 50}
                },
                "rest": "3:00 between rounds"
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 35
    },

    # שלישי 3
    {
        "exercises_used": ["Running", "Samson Lunge", "Superman Hold", "Plank Reach Through"],
        "training_program": {
            "3 rounds": {
                "round_target": {
                    "Running": {"distance": "200M", "notes": "jog"},
                    "Samson Lunge": {"time": "0:30", "notes": "stretch/leg"},
                    "Superman Hold": {"time": "0:30"},
                    "Plank Reach Through": {"reps": 10, "notes": "alternating"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Deadlift"],
        "training_program": {
            "strength": {
                "round_target": {
                    "Deadlift": {"scheme": "Build to 4@2RIR+ 2 x 3-4 reps", "percentage": "85%-90%"}
                }
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Knees to Elbow", "Row", "Assault Bike"],
        "training_program": {
            "In team of 2 16:00 AMRAP": {
                "round_target": {
                    "Knees to Elbow": {"reps": 40},
                    "Machine": {"distance": "2000/3000-meter Assault/1200/1500-meter row"}
                },
                "notes": [
                    "One person works at a time during the knees-to-elbows",
                    "One partner holds a plank while the other bikes/rows"
                ]
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 16
    },

    # רביעי 2
    {
        "exercises_used": ["Arm Circle", "Kettlebell Press", "Goblet Squat", "Push-up", "Wall Walk"],
        "training_program": {
            "3 sets": {
                "round_target": {
                    "Arm Circle": {"reps": 10, "notes": "forward and backward"},
                    "KB Press": {"reps": 15, "notes": "single-arm overhead"},
                    "Goblet Squat": {"reps": 5, "tempo": "@3000"},
                    "Push-up": {"reps": 5},
                    "Wall Walk": {"reps": 1}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 12
    },
    {
        "exercises_used": ["Back Squat"],
        "training_program": {
            "strength": {
                "round_target": {
                    "Back Squat": {"scheme": "Build to 4@1RIR+ 2-3 x 3-4 reps", "percentage": "85%-90%"}
                }
            }
        },
        "training_type": "strength",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Box Jump", "Handstand Push-up"],
        "training_program": {
            "Complete as many rounds as possible in 9:00 of": {
                "round_target": {
                    "Box Jump": {"reps": "2-4-6-8", "height": "60/50 CM"},
                    "Handstand Push-up": {"reps": "prescribed"}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 9
    },

    # שני 30
    {
        "exercises_used": ["Jump Around", "Jump Over", "Crawl Under"],
        "training_program": {
            "JUNKYARD DOG WARM-UP": {
                "round_target": {
                    "Partner A": {"reps": 6, "notes": "jumps around partner"},
                    "Partner B": {"reps": 6, "notes": "jumps around partner"},
                    "Partner A": {"reps": 4, "notes": "jump over and crawl under partner"},
                    "Partner B": {"reps": 4, "notes": "jump over and crawl under partner"}
                }
            }
        },
        "training_type": "warm-up",
        "training_source": "rocklee",
        "training_time": 10
    },
    {
        "exercises_used": ["Clean and Jerk"],
        "training_program": {
            "skill work": {
                "On a 10:00 clock": {
                    "Clean and Jerk": {"reps": 3, "notes": "unbroken", "notes2": "Build to a heavy set"}
                }
            }
        },
        "training_type": "skill",
        "training_source": "rocklee",
        "training_time": 15
    },
    {
        "exercises_used": ["Running", "Clean and Jerk"],
        "training_program": {
            "5 rounds for time": {
                "round_target": {
                    "Running": {"distance": "200m"},
                    "Clean and Jerk": {"reps": 6, "weight": "80/55 kg"}
                }
            }
        },
        "training_type": "metcon",
        "training_source": "rocklee",
        "training_time": 20
    }
]

ADDITION_LIST = [
    {
        "exercise_name": "Kettlebell Deadlift",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Lower back"]
    },
    {
        "exercise_name": "Bent Over Row",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Trapezius", "Rhomboids", "Rear Deltoids"]
    },
    {
        "exercise_name": "Dumbbell Shoulder Press",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Lateral deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Elbow To Instep",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Internal Obliques", "Hip Flexor"]
    },
    {
        "exercise_name": "Sumo Deadlift High Pull",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Trapezius"]
    },
    {
        "exercise_name": "Ring Muscle Up",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Trapezius", "Triceps Long Head", "Pectoralis major"]
    },
    {
        "exercise_name": "Ring Dip",
        "main_body_part": "triceps",
        "targeted_muscles": ["Triceps Long Head", "Triceps Lateral Head", "Pectoralis major"]
    },
    {
        "exercise_name": "Kipping Pull Up",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Trapezius", "Biceps Brachialis"]
    },
    {
        "exercise_name": "Deadlift",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Lower back", "Erector spinae"]
    },
    {
        "exercise_name": "Medicine Ball Pass",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "External Obliques"]
    },
    {
        "exercise_name": "Spiderman Twist",
        "main_body_part": "abs",
        "targeted_muscles": ["Internal Obliques", "External Obliques", "Hip Flexor"]
    },
    {
        "exercise_name": "Handstand",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Lateral deltoids", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Pvc Overhead Squat",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Kip Swing",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Side Tosses",
        "main_body_part": "abs",
        "targeted_muscles": ["External Obliques", "Internal Obliques"]
    },
    {
        "exercise_name": "Hollow",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis"]
    },
    {
        "exercise_name": "Butt Kicker",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Hip Flexor"]
    },
    {
        "exercise_name": "Jumping Jacks",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Bench Press",
        "main_body_part": "chest",
        "targeted_muscles": ["Pectoralis major", "Triceps Long Head", "Anterior deltoids"]
    },
    {
        "exercise_name": "High Pull",
        "main_body_part": "upper back",
        "targeted_muscles": ["Trapezius", "Rear Deltoids", "Hamstrings"]
    },
    {
        "exercise_name": "Crawl Under",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis"]
    },
    {
        "exercise_name": "Inchworm",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Hang Snatch",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Trapezius", "Shoulders"]
    },
    {
        "exercise_name": "Abmat Sit Up",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Hand Release Push Up",
        "main_body_part": "chest",
        "targeted_muscles": ["Pectoralis major", "Triceps Long Head"]
    },
    {
        "exercise_name": "Hang Power Clean",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Trapezius"]
    },
    {
        "exercise_name": "Split Jerk",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Lateral deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Pvc Switch",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Rotator cuff"]
    },
    {
        "exercise_name": "Bear Crawl",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis", "Quads"]
    },
    {
        "exercise_name": "Roll Pass",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "External Obliques"]
    },
    {
        "exercise_name": "Back Rack Lunge",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Behind Neck Press",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Lateral deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Muscle Snatch",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Trapezius", "Hamstrings"]
    },
    {
        "exercise_name": "Leg Swing",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Hip Flexor"]
    },
    {
        "exercise_name": "Front Scale",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Calf Raise",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Gastrocnemius", "Soleus"]
    },
    {
        "exercise_name": "Toy Soldiers",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Hip Flexor", "Quads"]
    },
    {
        "exercise_name": "Plank",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis"]
    },
    {
        "exercise_name": "Elbow Raises",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Lateral deltoids"]
    },
    {
        "exercise_name": "Single Leg Toe Touch",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes"]
    },
    {
        "exercise_name": "Handstand Push Up (HSPU)",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Triceps Long Head", "Rectus Abdominis"]
    },
    {
        "exercise_name": "V Up",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Alternating Lunges",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Power Clean",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Trapezius"]
    },
    {
        "exercise_name": "Strict Toes To Bar",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Spiderman Reaches",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Internal Obliques", "Hip Flexor"]
    },
    {
        "exercise_name": "Dumbbell Overhead Carry",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Lateral deltoids", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Up Downs",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Chest To Bar Pull Up",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Biceps Brachialis", "Trapezius"]
    },
    {
        "exercise_name": "Front Squat",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Thruster",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Anterior deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Down Dogs",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Hamstrings"]
    },
    {
        "exercise_name": "Goblet Squat",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Muscle Up",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Triceps Long Head", "Pectoralis major"]
    },
    {
        "exercise_name": "Butterfly Chest To Bar",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Biceps Brachialis"]
    },
    {
        "exercise_name": "Shoulder Press",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Lateral deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Pistol",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "L Sit",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Granny Tosses",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "External Obliques"]
    },
    {
        "exercise_name": "Single Leg Squat",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Russian Kettlebell Swing",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Lower back"]
    },
    {
        "exercise_name": "Dumbbell Farmers Carry",
        "main_body_part": "upper back",
        "targeted_muscles": ["Trapezius", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Squat Snatch",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis", "Shoulders"]
    },
    {
        "exercise_name": "Medicine Ball Squat",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Spiderman Stretch",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Internal Obliques", "Hip Flexor"]
    },
    {
        "exercise_name": "Weighted Ab Mat Sit Up",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Prisoner Squat",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Overhead Walking Lunge",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Anterior deltoids"]
    },
    {
        "exercise_name": "Single Dumbbell Press",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Pvc Overhead Lunges",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Glute Ham Developer Sit Up",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Push Up",
        "main_body_part": "chest",
        "targeted_muscles": ["Pectoralis major", "Triceps Long Head"]
    },
    {
        "exercise_name": "Dumbbell Clean And Jerk",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Trapezius", "Quads"]
    },
    {
        "exercise_name": "Toe Touch",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings"]
    },
    {
        "exercise_name": "Ring L Sit",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Plate",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis"]
    },
    {
        "exercise_name": "Clean And Jerk (C&J)",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Anterior deltoids", "Trapezius"]
    },
    {
        "exercise_name": "High Knees",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Hip Flexor", "Quads"]
    },
    {
        "exercise_name": "Rest",
        "main_body_part": "N/A",
        "targeted_muscles": []
    },
    {
        "exercise_name": "Scorpion Stretch",
        "main_body_part": "abs",
        "targeted_muscles": ["External Obliques", "Internal Obliques"]
    },
    {
        "exercise_name": "Air Squat",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Mountain Climbers",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Turkish Get Up",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis", "Quads"]
    },
    {
        "exercise_name": "Rope Climb",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Biceps Brachialis", "Trapezius"]
    },
    {
        "exercise_name": "Dumbbell Bench Press",
        "main_body_part": "chest",
        "targeted_muscles": ["Pectoralis major", "Triceps Long Head", "Anterior deltoids"]
    },
    {
        "exercise_name": "Strict Handstand Push Up",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Movement S",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis"]
    },
    {
        "exercise_name": "Samson Stretch",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Hip Flexor", "Quads"]
    },
    {
        "exercise_name": "Snatch",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Trapezius", "Shoulders"]
    },
    {
        "exercise_name": "Burpee",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis", "Pectoralis major"]
    },
    {
        "exercise_name": "Toes To Bar (T2B)",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Alternative Samson Lunges",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Hip Flexor"]
    },
    {
        "exercise_name": "Chest Passes",
        "main_body_part": "chest",
        "targeted_muscles": ["Pectoralis major"]
    },
    {
        "exercise_name": "Power Jerk",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Anterior deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Power Snatch",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Trapezius"]
    },
    {
        "exercise_name": "Medicine Ball Clean",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Walking Lunges",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Karaoke",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Hip Flexor"]
    },
    {
        "exercise_name": "Band Pull Apart",
        "main_body_part": "upper back",
        "targeted_muscles": ["Rear Deltoids", "Trapezius"]
    },
    {
        "exercise_name": "Bar Muscle Up",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Triceps Long Head", "Pectoralis major"]
    },
    {
        "exercise_name": "Front Rack",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Leg Press",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Front Rack Carry",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Plate Ground To Overhead",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Trapezius"]
    },
    {
        "exercise_name": "Plank Reach Through",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "External Obliques", "Internal Obliques"]
    },
    {
        "exercise_name": "Handstand Walk",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Push Press",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Anterior deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Dumbbell Power Clean",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Trapezius"]
    },
    {
        "exercise_name": "Hang Clean And Jerk",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Anterior deltoids", "Trapezius"]
    },
    {
        "exercise_name": "Strict Pull Up",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Biceps Brachialis"]
    },
    {
        "exercise_name": "Hollow Rock",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis"]
    },
    {
        "exercise_name": "Kettlebell Presses",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Counterbalance Squat",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Back Extension",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Lower back", "Glutes", "Hamstrings"]
    },
    {
        "exercise_name": "Dumbbell Romanian Deadlift",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Lower back"]
    },
    {
        "exercise_name": "Butterfly Pull Up",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Biceps Brachialis"]
    },
    {
        "exercise_name": "Knee To Chest",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Box Jump",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Dumbbell Press",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Pvc Movements",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Rotator cuff"]
    },
    {
        "exercise_name": "Back Rack Position",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Pvc Good Mornings",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Lower back"]
    },
    {
        "exercise_name": "Jumping Squat",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Ring Support",
        "main_body_part": "triceps",
        "targeted_muscles": ["Triceps Long Head", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Wall Ball",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis", "Shoulders"]
    },
    {
        "exercise_name": "Dragon Flag",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis"]
    },
    {
        "exercise_name": "Strict Press",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Underhand Toss",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "External Obliques"]
    },
    {
        "exercise_name": "Row",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Trapezius", "Rhomboids"]
    },
    {
        "exercise_name": "Good Mornings",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Lower back", "Glutes"]
    },
    {
        "exercise_name": "Dumbbell Snatch",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Trapezius"]
    },
    {
        "exercise_name": "Knees To Elbows",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Single Unders",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Skin The Cat",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Shoulders"]
    },
    {
        "exercise_name": "Dumbbell Suitcase Carry",
        "main_body_part": "abs",
        "targeted_muscles": ["Transverse Abdominis", "Rectus Abdominis", "Trapezius"]
    },
    {
        "exercise_name": "Ring Row",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Trapezius", "Biceps Brachialis"]
    },
    {
        "exercise_name": "Kettlebell Front Rack",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Push Jerk",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Anterior deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Double Unders",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Superman",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Lower back", "Glutes"]
    },
    {
        "exercise_name": "Pvc Pass Throughs",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Rotator cuff", "Anterior deltoids"]
    },
    {
        "exercise_name": "Twist",
        "main_body_part": "abs",
        "targeted_muscles": ["External Obliques", "Internal Obliques"]
    },
    {
        "exercise_name": "Box Step Up",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Back Squat",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Dumbbell Reverse Lunge",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Clean",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Trapezius"]
    },
    {
        "exercise_name": "Bar Facing Burpee",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis", "Pectoralis major"]
    },
    {
        "exercise_name": "Down And Back Movements",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis"]
    },
    {
        "exercise_name": "Farmers Carry",
        "main_body_part": "abs",
        "targeted_muscles": ["Transverse Abdominis", "Rectus Abdominis", "Trapezius"]
    },
    {
        "exercise_name": "Scap Pull Up",
        "main_body_part": "upper back",
        "targeted_muscles": ["Trapezius", "Latissimus Dorsi"]
    },
    {
        "exercise_name": "Kettlebell Swing",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Lower back"]
    },
    {
        "exercise_name": "Pvc",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Rotator cuff"]
    },
    {
        "exercise_name": "Hang Clean",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Trapezius"]
    },
    {
        "exercise_name": "Pull Up",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Biceps Brachialis"]
    },
    {
        "exercise_name": "Jump Rope",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Legless Rope Climb",
        "main_body_part": "upper back",
        "targeted_muscles": ["Latissimus Dorsi", "Biceps Brachialis"]
    },
    {
        "exercise_name": "Kettlebell Clean",
        "main_body_part": "posterior chain",
        "targeted_muscles": ["Hamstrings", "Glutes", "Trapezius"]
    },
    {
        "exercise_name": "Shuttle Run",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Knee Push Up",
        "main_body_part": "chest",
        "targeted_muscles": ["Pectoralis major", "Triceps Long Head"]
    },
    {
        "exercise_name": "Devil Press",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Anterior deltoids", "Pectoralis major"]
    },
    {
        "exercise_name": "Single Leg V Ups",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Squat Toss",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Dumbbell Front Rack",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Spiderman Lunge",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Hip Flexor"]
    },
    {
        "exercise_name": "Step Up",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Side Pass",
        "main_body_part": "abs",
        "targeted_muscles": ["External Obliques", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Run",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Jog",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Shoulder To Overhead",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Triceps Long Head"]
    },
    {
        "exercise_name": "Front Rack Lunge",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Arm Circles",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Lateral deltoids", "Rotator cuff"]
    },
    {
        "exercise_name": "Overhead Squat (OHS)",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Rectus Abdominis", "Anterior deltoids"]
    },
    {
        "exercise_name": "Reverse Lunge",
        "main_body_part": "anterior chain",
        "targeted_muscles": ["Quads", "Legs"]
    },
    {
        "exercise_name": "Deficit Handstand Push Up",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Triceps Long Head", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Wall Walk",
        "main_body_part": "shoulders",
        "targeted_muscles": ["Anterior deltoids", "Rectus Abdominis"]
    },
    {
        "exercise_name": "Sit Ups",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Hip Flexor"]
    },
    {
        "exercise_name": "Crab Walk",
        "main_body_part": "abs",
        "targeted_muscles": ["Rectus Abdominis", "Transverse Abdominis", "Quads"]
    }
]

NEW_EXERCISES = {
  "Iso Lateral Kneeling Leg Curl": {
    "tips": [
      "Keep hips pressed against the pad throughout the movement",
      "Avoid using momentum to complete the curl",
      "Focus on hamstring contraction rather than weight moved",
      "Control the negative (eccentric) portion of the exercise"
    ],
    "equipment": ["Iso Lateral Leg Curl Machine"],
    "main_body_part": "Posterior Chain",
    "targeted_muscles": ["Hamstrings", "Glutes", "Calves"],
    "expertise": 3,
    "demo_url": "https://www.youtube.com/watch?v=ELOCsoDSmrg",
    "body_part": ["Legs"],
    "favorite": False,
    "description": [
      "Adjust the machine for your height with knees aligned with pivot point",
      "Kneel on the pad with ankles secured under the roller pads",
      "Position hips firmly against the support pad",
      "Grasp handles for stability if available",
      "Flex knees to curl the weight toward your glutes",
      "Maintain tension as you curl to full contraction",
      "Hold the contracted position briefly at the top",
      "Lower the weight with control to starting position",
      "Repeat for prescribed repetitions with proper form"
    ]
  }
}
# print([keys for keys in NEW_EXERCISES.keys()])
