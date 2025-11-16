"""
Example Data from Paper
示例数据来源于论文

Source: "GenAI Advertising: Risks of Personalizing Ads with LLMs"
Paper: arXiv:2409.15436v1
Appendix A.4: Generated User Profiles From Study

This file contains real user profiles generated during the paper's user study,
plus example products mentioned in the research.
"""

# ============================================================================
# USER PROFILES FROM PAPER (Appendix A.4)
# ============================================================================

# User Profile 1: Mid-late 20s Male, Engineering/Tech Interest
USER_PROFILE_1 = {
    "demographics": {
        "age": "Mid to late 20s",
        "gender": "Male",
        "location": "Possibly a university setting or recent graduate",
        "occupation": "Interest in engineering or technology",
        "ethnicity": "Not specified"
    },
    "interests": {
        "interests_includes": [
            "Basketball",
            "Avatar: The Last Airbender TV show",
            "Physical fitness and health",
            "NBA history and timeline"
        ],
        "interests_likely": [
            "Professional development",
            "Avoiding product promotions",
            "Efficiency in communication"
        ]
    },
    "personality_traits": {
        "personality_characteristics": [
            "Assertive in communication",
            "Detail-oriented",
            "Focused on self-improvement",
            "Preferential towards direct responses without unnecessary information"
        ],
        "personality_likely": [
            "Skeptical or cautious of AI features",
            "Possibly frustrated with repetition or lack of adherence to instructions",
            "Possesses a level of perseverance and determination"
        ]
    }
}

# String format for use in prompts
USER_PROFILE_1_STR = """Male, Mid to late 20s
Interested in: Basketball, Avatar: The Last Airbender, Physical fitness, NBA history
Personality: Assertive, Detail-oriented, Focused on self-improvement"""

# User Profile 2: 30-40 Female, Healthcare/Hospitality Professional
USER_PROFILE_2 = {
    "demographics": {
        "age": "30-40",
        "gender": "Female",
        "location": "Unknown",
        "occupation": "Nurse and Chef/Manager in Hospitality Industry",
        "ethnicity": "Unknown"
    },
    "interests": {
        "health_and_medicine": [
            "Balanced living routines",
            "Autoimmune diseases"
        ],
        "time_management": [
            "PhD in Health and Medicine"
        ],
        "creativity": [
            "Writing short stories"
        ],
        "socializing": [
            "Planning activities for friends and family"
        ]
    },
    "personality_traits": {
        "organized": [
            "Creating timetables for PhD studies",
            "Planning activities for friends and family"
        ],
        "empathetic": [
            "Nurse profession"
        ],
        "creative": [
            "Writing short stories about social issues like racism"
        ],
        "diligent": [
            "Performance reviews for work evaluation"
        ]
    }
}

USER_PROFILE_2_STR = """Female, 30-40
Occupation: Nurse and Chef/Manager
Interests: Health, Medicine, Autoimmune diseases, Writing, Planning events
Personality: Organized, Empathetic, Creative, Diligent"""

# User Profile 3: Late 20s-Early 40s Female, Legal Professional
USER_PROFILE_3 = {
    "demographics": {
        "age": "Late 20s to early 40s",
        "gender": "Female",
        "location": "Moving from Houston to Washington DC",
        "occupation": "Legal support professional",
        "ethnicity": "Not specified"
    },
    "interests": {
        "moving_city_exploration": [
            "Interested in exploring Washington DC",
            "Curious about equivalent stores in DC compared to Houston"
        ],
        "professional_development": [
            "Seeking courses and videos tailored to legal support professionals",
            "Interested in free classes for Microsoft skills"
        ],
        "cultural_experiences": [
            "Drawn to African American culture and heritage"
        ],
        "creative_writing": [
            "Enjoy writing short stories"
        ],
        "travel": [
            "Interested in weekend getaways like a trip to Nashville, Tennessee"
        ]
    },
    "personality_traits": {
        "curious": "Shows curiosity through questions about markets, classes, and locations",
        "organized": "Enjoys planning and outlining, demonstrated by requests for itineraries and lecture outlines",
        "creative": "Displays creativity through requests for writing a short story"
    }
}

USER_PROFILE_3_STR = """Female, Late 20s to early 40s
Occupation: Legal support professional
Location: Moving from Houston to Washington DC
Interests: City exploration, Professional development, African American culture, Writing, Travel
Personality: Curious, Organized, Creative"""

# User Profile 4: 55 Female, Division Manager
USER_PROFILE_4 = {
    "Demographics": {
        "Age": "55 years old",
        "Gender": "Female",
        "Occupation": "Division Manager in Capital Projects at a Water Company",
        "Location": "Unknown",
        "Ethnicity": "Unknown"
    },
    "Interests": {
        "Interests": [
            "Post-apocalyptic fiction",
            "Writing",
            "Reflection on humanity",
            "Exploring darker aspects of humanity",
            "Narratives that push characters to their limits"
        ]
    },
    "Personality Traits": {
        "Personality Traits": [
            "Curious",
            "Thoughtful",
            "Reflective",
            "Obsessive",
            "Analytical",
            "Creative"
        ]
    }
}

USER_PROFILE_4_STR = """Female, 55 years old
Occupation: Division Manager in Capital Projects at a Water Company
Interests: Post-apocalyptic fiction, Writing, Reflection on humanity
Personality: Curious, Thoughtful, Reflective, Analytical, Creative"""

# User Profile 5: 30-40 Male, Sports Enthusiast
USER_PROFILE_5 = {
    "demographics": {
        "age": "30-40",
        "gender": "Male",
        "location": "Portland, Oregon",
        "occupation": "Unknown",
        "ethnicity": "Caucasian"
    },
    "interests": {
        "sports": [
            "Basketball",
            "NBA"
        ],
        "players": [
            "Aaron Judge",
            "Shohei Ohtani",
            "Klay Thompson"
        ],
        "teams": [
            "Golden State Warriors"
        ],
        "movies_books": [
            "Enjoys watching movies and reading books"
        ],
        "relocation": [
            "Interested in moving to a new town/city"
        ]
    },
    "personality_traits": {
        "inquisitive": True,
        "sports_enthusiast": True,
        "detail-oriented": True,
        "assertive": True
    }
}

USER_PROFILE_5_STR = """Male, 30-40
Location: Portland, Oregon
Interests: Basketball, NBA, Golden State Warriors, Aaron Judge, Shohei Ohtani
Personality: Inquisitive, Sports enthusiast, Detail-oriented, Assertive"""

# ============================================================================
# EXAMPLE PRODUCTS (from paper)
# ============================================================================

# Example product from paper (mentioned in data_driven.py)
EXAMPLE_PRODUCT = {
    "product": "Coursera",
    "url": "https://www.coursera.org/",
    "desc": "Online learning platform offering courses from top universities"
}

# Products by category (examples from Figure 13 in paper)
PRODUCTS = {
    "technology": [
        {"name": "Python", "url": "https://www.python.org/", "desc": "Programming language for data science and web development"},
        {"name": "Microsoft", "url": "https://www.microsoft.com/", "desc": "Technology company offering software and cloud services"},
        {"name": "HP", "url": "https://www.hp.com/", "desc": "Computer hardware manufacturer"},
        {"name": "Intel", "url": "https://www.intel.com/", "desc": "Semiconductor chip manufacturer"},
        {"name": "Apple", "url": "https://www.apple.com/", "desc": "Consumer electronics and software company"},
    ],
    "education": [
        {"name": "Coursera", "url": "https://www.coursera.org/", "desc": "Online learning platform"},
        {"name": "MasterClass", "url": "https://www.masterclass.com/", "desc": "Online classes from world-renowned instructors"},
        {"name": "LinkedIn Learning", "url": "https://www.linkedin.com/learning/", "desc": "Professional development courses"},
    ],
    "entertainment": [
        {"name": "Netflix", "url": "https://www.netflix.com/", "desc": "Streaming service for movies and TV shows"},
        {"name": "HBO", "url": "https://www.hbo.com/", "desc": "Premium entertainment network"},
        {"name": "IMDB", "url": "https://www.imdb.com/", "desc": "Movie and TV show database"},
    ],
    "shopping": [
        {"name": "Amazon", "url": "https://www.amazon.com/", "desc": "Online retail marketplace"},
        {"name": "Target", "url": "https://www.target.com/", "desc": "Retail corporation"},
        {"name": "Etsy", "url": "https://www.etsy.com/", "desc": "Marketplace for handmade and vintage items"},
    ],
    "travel": [
        {"name": "Airbnb", "url": "https://www.airbnb.com/", "desc": "Vacation rental platform"},
        {"name": "Lonely Planet", "url": "https://www.lonelyplanet.com/", "desc": "Travel guides and information"},
    ]
}

# All profiles in a list
ALL_USER_PROFILES = [
    USER_PROFILE_1,
    USER_PROFILE_2,
    USER_PROFILE_3,
    USER_PROFILE_4,
    USER_PROFILE_5
]

ALL_USER_PROFILES_STR = [
    USER_PROFILE_1_STR,
    USER_PROFILE_2_STR,
    USER_PROFILE_3_STR,
    USER_PROFILE_4_STR,
    USER_PROFILE_5_STR
]
