"""translations.py -- English for the content that came out of cbg1.xlsx.

Task titles, deliverables, notes and people's names are free text, so they cannot be
mapped by a vocabulary the way statuses and areas are. They are translated ONCE here
and written into the CSV as `*_en` columns by import_excel.py, which means:

  * the English is DATA -- visible in the sheet, correctable by the team, and
    reviewable in a diff -- rather than something the app invents at render time;
  * a task added later through the app simply carries whatever English the person
    typed, and falls back to the Hebrew when they typed none, so nothing ever
    disappears from the board.

TWO THINGS NEED A HUMAN EYE (both marked below):
  * T05's Hebrew note is garbled in the source workbook. The English is a best
    reading of the intent, not a translation of what is written.
  * "שיקר" is transliterated as "Shikar". It is an unusual name and may be a typo
    in the workbook; correct it in people.csv if so.
"""

# task id -> English for the three free-text fields
TASKS_EN = {
    "T01": {"title": "Doll detection",
            "deliverable": "Detect the object intended for grasping",
            "notes": "The link between the doll and the box needs clarifying"},
    "T02": {"title": "Grasp the doll off a table",
            "deliverable": "Grasp the object that was detected"},
    "T03": {"title": "Steer navigation to the grasping position",
            "deliverable": "Guidance to the table and to a pose suitable for grasping",
            "notes": "Includes coordination with the navigation team"},
    "T04": {"title": "Floor-level localization using Wi-Fi",
            "deliverable": "Locate the robot in space from Wi-Fi data",
            "notes": "Currently based on three routers for the whole floor"},
    "T05": {"title": "Extend to a larger number of Wi-Fi routers",
            "deliverable": "Localization from many routers instead of three per floor",
            # The Hebrew here is garbled in cbg1.xlsx; read as "we have not yet found
            # where to buy the routers". Check against what was meant.
            "notes": "No source found yet for buying the routers (Hebrew note is "
                     "garbled in the source file — please check)"},
    "T06": {"title": "Collision-free motion",
            "deliverable": "Safe local navigation along the trial route"},
    "T07": {"title": "Reach the target room",
            "deliverable": "Reach the chosen room while avoiding obstacles",
            "notes": "The dependencies are a proposal, for coordination"},
    "T08": {"title": "Approach the table in order to grasp",
            "deliverable": "Stop at a suitable pose facing the table",
            "notes": "Coordinate with the detection and grasping team"},
    "T09": {"title": "Carry the box and set it down in another room",
            "deliverable": "Carry and place the box in the target room",
            "notes": "The area assignment is provisional. Grasping a box versus a "
                     "doll needs clarifying"},
    "T10": {"title": "End-to-end integrated trial",
            "deliverable": "Demonstrate the full sequence: navigate, grasp, carry, place",
            "notes": "Agree success criteria and a date together with the teams"},
    "T11": {"title": "Use the mobile camera in place of the memory component",
            "deliverable": "Integrate the mobile camera into local navigation as a "
                           "replacement for the memory component"},
    "T12": {"title": "Localization using LiDAR",
            "deliverable": "Estimate the robot's position using LiDAR"},
    "T13": {"title": "Build a flexible, modular vision-based navigation app",
            "deliverable": "Vision-based navigation app with interchangeable modular "
                           "components"},
    "T14": {"title": "Build an app to start the robot and connect to it",
            "deliverable": "App that starts the robot and opens a connection to it"},
    "T15": {"title": "Add obstacle avoidance using LiDAR",
            "deliverable": "Option to use LiDAR for avoiding obstacles"},
}

# Hebrew name -> English. Transliterations, so they are worth a second look.
NAMES_EN = {
    "שירה": "Shira",
    "מקסים": "Maxim",
    "ליאור": "Lior",
    "איתי": "Itai",
    "דויד": "David",
    "דניאל": "Daniel",
    "פנחס": "Pinchas",
    "יהונתן": "Yehonatan",
    "אליאס": "Elias",
    "שיקר": "Shikar",        # unusual; possibly a typo in cbg1.xlsx
}
