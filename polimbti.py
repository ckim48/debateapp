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
        "description": "Passionate about progressive values, global cooperation, and community-based regulation.",
        "caution": "May benefit from grounding ideals with practical experience."
    },
    "EPGI": {
        "nickname": "Visionary Advocate",
        "careers": ["Activist", "Human Rights Lawyer", "Political Strategist"],
        "compatible_countries": ["Canada", "Denmark", "Germany"],
        "description": "Driven by global justice and personal freedom, with a strong belief in social progress.",
        "caution": "May need to consider diverse perspectives when advocating change."
    },
    "EPNR": {
        "nickname": "Inclusive Patriot",
        "careers": ["Public Educator", "Community Organizer", "Ethics Advisor"],
        "compatible_countries": ["Finland", "Ireland", "South Korea"],
        "description": "Supports cultural identity and national integrity while embracing inclusive progress.",
        "caution": "May face challenges reconciling tradition with evolving norms."
    },
    "EPNI": {
        "nickname": "Justice Crusader",
        "careers": ["Public Defender", "Policy Campaigner", "Civic Educator"],
        "compatible_countries": ["Norway", "France", "Japan"],
        "description": "Strong advocate for national integrity and freedom with an emphasis on ethical reform.",
        "caution": "May occasionally struggle with compromise in policy discussions."
    },
    "ECGR": {
        "nickname": "Community Guardian",
        "careers": ["Local Government Official", "Social Services Director", "School Principal"],
        "compatible_countries": ["South Korea", "Austria", "Taiwan"],
        "description": "Values social stability and shared responsibility within cultural traditions.",
        "caution": "May prefer familiar systems over bold innovation."
    },
    "ECGI": {
        "nickname": "Principled Conservative",
        "careers": ["Constitutional Lawyer", "Ethics Committee Advisor", "Traditional Media Columnist"],
        "compatible_countries": ["Poland", "Hungary", "United States"],
        "description": "Upholds traditional values and individual liberty with a strong ethical framework.",
        "caution": "May benefit from balancing values with adaptability."
    },
    "ECNR": {
        "nickname": "Localist Mediator",
        "careers": ["City Council Member", "Small Business Advocate", "Cultural Heritage Officer"],
        "compatible_countries": ["Japan", "Greece", "Spain"],
        "description": "Focuses on cultural preservation, local autonomy, and community-driven governance.",
        "caution": "May find global trends challenging to integrate locally."
    },
    "ECNI": {
        "nickname": "Doctrinal Nationalist",
        "careers": ["National Security Analyst", "Political Columnist", "Legal Enforcer"],
        "compatible_countries": ["Russia", "China", "Iran"],
        "description": "Strongly prioritizes sovereignty, tradition, and national unity through structured policy.",
        "caution": "May need to ensure inclusive dialogue in national policy."
    },
    "FPGR": {
        "nickname": "Market Innovator",
        "careers": ["Tech Entrepreneur", "Startup Consultant", "Innovation Officer"],
        "compatible_countries": ["Singapore", "Estonia", "United States"],
        "description": "Emphasizes economic freedom, global innovation, and pragmatic social growth.",
        "caution": "May sometimes underplay social impacts of disruption."
    },
    "FPGI": {
        "nickname": "Liberal Internationalist",
        "careers": ["Diplomat", "Global Policy Analyst", "Tech Policy Director"],
        "compatible_countries": ["United Kingdom", "Canada", "Switzerland"],
        "description": "Champions open economies, global cooperation, and individual rights.",
        "caution": "May need to be mindful of local sensitivities in global work."
    },
    "FPNR": {
        "nickname": "Pragmatic Modernist",
        "careers": ["Management Consultant", "Policy Advisor", "Urban Designer"],
        "compatible_countries": ["South Korea", "Germany", "Netherlands"],
        "description": "Seeks practical solutions for modern society while preserving cultural identity.",
        "caution": "May benefit from defining long-term principles more clearly."
    },
    "FPNI": {
        "nickname": "Freedom Strategist",
        "careers": ["Think Tank Fellow", "Security Advisor", "Military Strategist"],
        "compatible_countries": ["United States", "Israel", "South Korea"],
        "description": "Focused on security, personal freedom, and national independence.",
        "caution": "May need to ensure liberty-focused policies remain balanced."
    },
    "FCGR": {
        "nickname": "Classic Realist",
        "careers": ["Civil Servant", "Fiscal Analyst", "Public Safety Officer"],
        "compatible_countries": ["Japan", "Germany", "Czech Republic"],
        "description": "Grounded in order, regulation, and economic realism with a cultural foundation.",
        "caution": "May occasionally overlook emerging cultural or social changes."
    },
    "FCGI": {
        "nickname": "Liberty Defender",
        "careers": ["Constitutional Scholar", "Defense Advisor", "Opinion Writer"],
        "compatible_countries": ["USA", "Australia", "UK"],
        "description": "Committed to individual liberty, cultural traditions, and strong institutions.",
        "caution": "May want to balance consistency with flexibility in debates."
    },
    "FCNR": {
        "nickname": "Hawkish Libertarian",
        "careers": ["Policy Analyst", "Economic Development Lead", "Freedom Lobbyist"],
        "compatible_countries": ["South Korea", "USA", "Taiwan"],
        "description": "Advocates for economic liberty, national strength, and practical governance.",
        "caution": "May need to weigh economic freedom against social impact."
    },
    "FCNI": {
        "nickname": "Sovereign Purist",
        "careers": ["Border Policy Director", "Defense Strategist", "National Affairs Editor"],
        "compatible_countries": ["Hungary", "Russia", "India"],
        "description": "Strong supporter of national sovereignty, tradition, and cultural integrity.",
        "caution": "May benefit from fostering cross-cultural understanding."
    }
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
        "caution": profile.get("caution", "No data available."),
        "description": profile.get("description", "No data available.")
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
