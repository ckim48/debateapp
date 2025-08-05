# axes for selecting alphabet depending on the result of question set
axes = {
    "E_vs_F": ("E", "F"),
    "P_vs_C": ("P", "C"),
    "G_vs_N": ("G", "N"),
    "R_vs_I": ("R", "I"),
}

# indices for each question with grouping
axis_indices = {
    "E_vs_F": [ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    "P_vs_C": [10, 11, 12, 13, 24, 25, 26, 27, 28, 29, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69],
    "G_vs_N": [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 70, 71, 72, 73, 74, 75, 76, 77],
    "R_vs_I": [42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 78, 79],
}
axis_category_map = {
    "E_vs_F": ["Economy", "Freedom"],
    "P_vs_C": ["Progress", "Culture"],
    "G_vs_N": ["Globalism", "Nationalism"],
    "R_vs_I": ["Regulation", "Individualism"]
}
# profile dictionary with given politics character
political_profiles = {
    "EPGR": {
        "nickname": "Idealistic Reformer",
        "careers": ["Social Policy Analyst", "NGO Worker", "Urban Planner"],
        "compatible_countries": ["Sweden", "Netherlands", "New Zealand"],
        "caution": "May become overly idealistic and disconnected from political realities."
    },
    "EPGI": {
        "nickname": "Visionary Advocate",
        "careers": ["Activist", "Human Rights Lawyer", "Political Strategist"],
        "compatible_countries": ["Canada", "Denmark", "Germany"],
        "caution": "Tendency to be rigid or confrontational when ideals are challenged."
    },
    "EPNR": {
        "nickname": "Inclusive Patriot",
        "careers": ["Public Educator", "Community Organizer", "Ethics Advisor"],
        "compatible_countries": ["Finland", "Ireland", "South Korea"],
        "caution": "Struggles with balancing national identity and openness to change."
    },
    "EPNI": {
        "nickname": "Justice Crusader",
        "careers": ["Public Defender", "Policy Campaigner", "Civic Educator"],
        "compatible_countries": ["Norway", "France", "Japan"],
        "caution": "Can alienate others with uncompromising or radical positions."
    },
    "ECGR": {
        "nickname": "Community Guardian",
        "careers": ["Local Government Official", "Social Services Director", "School Principal"],
        "compatible_countries": ["South Korea", "Austria", "Taiwan"],
        "caution": "May resist necessary reforms or modernizations due to comfort with tradition."
    },
    "ECGI": {
        "nickname": "Principled Conservative",
        "careers": ["Constitutional Lawyer", "Ethics Committee Advisor", "Traditional Media Columnist"],
        "compatible_countries": ["Poland", "Hungary", "United States"],
        "caution": "May overprioritize ideology at the cost of practical governance."
    },
    "ECNR": {
        "nickname": "Localist Mediator",
        "careers": ["City Council Member", "Small Business Advocate", "Cultural Heritage Officer"],
        "compatible_countries": ["Japan", "Greece", "Spain"],
        "caution": "Can become resistant to external influence or globalization."
    },
    "ECNI": {
        "nickname": "Doctrinal Nationalist",
        "careers": ["National Security Analyst", "Political Columnist", "Legal Enforcer"],
        "compatible_countries": ["Russia", "China", "Iran"],
        "caution": "May trend toward authoritarian or exclusionary policies."
    },
    "FPGR": {
        "nickname": "Market Innovator",
        "careers": ["Tech Entrepreneur", "Startup Consultant", "Innovation Officer"],
        "compatible_countries": ["Singapore", "Estonia", "United States"],
        "caution": "Risk of overlooking social inequality in pursuit of growth."
    },
    "FPGI": {
        "nickname": "Liberal Internationalist",
        "careers": ["Diplomat", "Global Policy Analyst", "Tech Policy Director"],
        "compatible_countries": ["United Kingdom", "Canada", "Switzerland"],
        "caution": "May face backlash for globalism in nationalist-leaning societies."
    },
    "FPNR": {
        "nickname": "Pragmatic Modernist",
        "careers": ["Management Consultant", "Policy Advisor", "Urban Designer"],
        "compatible_countries": ["South Korea", "Germany", "Netherlands"],
        "caution": "May struggle with long-term vision or ideological clarity."
    },
    "FPNI": {
        "nickname": "Freedom Strategist",
        "careers": ["Think Tank Fellow", "Security Advisor", "Military Strategist"],
        "compatible_countries": ["United States", "Israel", "South Korea"],
        "caution": "Tends to justify intrusive policies in name of liberty or order."
    },
    "FCGR": {
        "nickname": "Classic Realist",
        "careers": ["Civil Servant", "Fiscal Analyst", "Public Safety Officer"],
        "compatible_countries": ["Japan", "Germany", "Czech Republic"],
        "caution": "May ignore emerging cultural shifts or public sentiment."
    },
    "FCGI": {
        "nickname": "Liberty Defender",
        "careers": ["Constitutional Scholar", "Defense Advisor", "Opinion Writer"],
        "compatible_countries": ["USA", "Australia", "UK"],
        "caution": "Risk of rigidity and ideological tribalism."
    },
    "FCNR": {
        "nickname": "Hawkish Libertarian",
        "careers": ["Policy Analyst", "Economic Development Lead", "Freedom Lobbyist"],
        "compatible_countries": ["South Korea", "USA", "Taiwan"],
        "caution": "May ignore social consequences of economic policies."
    },
    "FCNI": {
        "nickname": "Sovereign Purist",
        "careers": ["Border Policy Director", "Defense Strategist", "National Affairs Editor"],
        "compatible_countries": ["Hungary", "Russia", "India"],
        "caution": "Prone to xenophobia or civil liberty restrictions."
    },
}
def calculate_political_type_from_categories(category_avg):
    result_code = ""

    for axis_key, (left, right) in axes.items():
        related_categories = axis_category_map.get(axis_key, [])
        scores = [category_avg.get(cat, 3.0) for cat in related_categories]  # default to neutral
        avg = sum(scores) / len(scores) if scores else 3.0
        result_code += left if avg <= 3 else right

    profile = political_profiles.get(result_code, {})
    return {
        "code": result_code,
        "nickname": profile.get("nickname", "Unknown"),
        "careers": profile.get("careers", []),
        "countries": profile.get("compatible_countries", []),
        "caution": profile.get("caution", "No data available.")
    }

def calculate_political_type(responses):
    """
    responses: List of 80 integers (Likert scale 1(strongly disagree) ~ 5(strongly agree))
    return: dict with result_code and profile info
    """
    if len(responses) != 80:
        raise ValueError("The response length is not 80.")

    result_code = ""

    for axis_key, (left_letter, right_letter) in axes.items():
        indices = axis_indices[axis_key]
        total = sum(responses[i] for i in indices)
        avg = total / len(indices)
        if avg <= 3:
            result_code += left_letter
        else:
            result_code += right_letter

    # getting pf result
    profile = political_profiles.get(result_code, {})
    return {
        "code": result_code,
        "nickname": profile.get("nickname", "Unknown"),
        "careers": profile.get("careers", []),
        "countries": profile.get("compatible_countries", []),
        "caution": profile.get("caution", "No data available.")
    }


if __name__ == "__main__":
    # For test: all 3
    example_responses = [3] * 80
    result = calculate_political_type(example_responses)

    print("Political code:", result["code"])
    print("Nickname:", result["nickname"])
    print("Recommended Job:", ", ".join(result["careers"]))
    print("countries with similar character:", ", ".join(result["countries"]))
    print("cautions:", result["caution"])
