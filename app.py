import os
from flask import Flask, jsonify, request
import requests
import json
from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.prompts import PromptTemplate
from flask_cors import CORS
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)
llm = ChatGroq(
    groq_api_key="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",
    model="llama3-8b-8192",
    temperature=0.2,
)

def extract_company_description(url):
    loader = WebBaseLoader(url)
    page_data = loader.load().pop().page_content

    prompt_extract = PromptTemplate.from_template(
        """
    ### SCRAPED TEXT FROM WEBSITE:
    {page_data}
    ### INSTRUCTION:
    The scraped text is from the "About Us" page of a company's website. Your task is to thoroughly analyze the content and write a detailed description about the company in a professional tone. The description should:
    - Be a minimum of 250 words.
    - Explain what the company does, including its core services, products, and areas of expertise.
    - Highlight the company's mission, vision, and values if mentioned.
    - Mention key achievements, clients, or partnerships if provided in the text.
    - Use clear, concise, and professional language.

    Return the detailed description as plain text (do not format it as JSON).
    """
    )
    chain_extract = prompt_extract | llm
    res = chain_extract.invoke(input={"page_data": page_data})

    company_description = {
        "name": url, 
        "company_desc": res.content.strip()
    }

    return company_description

def extract_company_technology(url):
    api_key = "0fe0b1c2-9db3-4ff5-abfd-da04fe679043"
    url = f"https://api.builtwith.com/v21/api.json?KEY={api_key}&LOOKUP={url}"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error retrieving data from BuiltWith API: {e}"}

    data = response.json()
    processed_data = {}

    if "Results" in data and len(data["Results"]) > 0:
        paths = data["Results"][0]["Result"].get("Paths", [])

        for index, path in enumerate(paths):
            technologies = path.get("Technologies", [])
            limit = 30 if index == 0 else 15

            for tech in technologies[:limit]:
                if "Categories" in tech:
                    category_value = ", ".join(tech["Categories"])
                    processed_data[category_value] = tech["Name"]
                elif "Name" in tech:
                    processed_data[tech["Name"]] = tech["Name"]

    return processed_data

def suggest_better_technologies(company_info, technology_info):
    prompt_suggestion = PromptTemplate.from_template(
    """
    ### COMPANY DESCRIPTION:
    {company_desc}

    ### TECHNOLOGIES USED:
    {technology_info}

    ### INSTRUCTION:
    Based on the company description and the technologies currently being used in thiere website, evaluate the technologies in three categories for their website:

    1. **BetterReplace**: Identify at least 10 technologies that should be replaced with better alternatives. For each replacement, do the following:
       - Provide the suggested new technology with its name and version Replace current technology with a completely new tech stack instead of just version updates.
       - Compare it with the current technology and explain why the suggested new technology is superior.
       - Highlight the advantages it offers to the company in terms of performance, scalability, cost-effectiveness, security, or user experience. Specifically explain how the replacement can directly benefit the companys website and business operations such as Improving website speed, uptime, or responsiveness ,Enhancing security to protect customer data and build trust Reducing operational costs through automation or more efficient resource management,Enhancing user experience to increase conversions or customer satisfaction Ensuring scalability for future growth without compromising performance,Consider the industry and the specific challenges the company may face.

    2.GoodToUse: List the technologies that are currently being used and are well-suited for the company based on its description. No changes are required for these technologies.

    3.SuggestionToAddNewTech: Suggest at least 5 new technologies that are not currently being used but could benefit the company. For each suggestion:
       - Provide the name of the new technology.
       - Explain its benefits and why it should be added.

   Return the suggestions in the following JSON format:
    {{
        "BetterReplace": [
            {{
                "technology": "Suggested technology name and version",
                "comparison": "Current technology: Current technology name and version",
                "benefits": "Key advantages of switching to the suggested technology for my website and business."
            }},
            ...
        ],
        "GoodToUse": [
            "Current technology name 1",
            "Current technology name 2",
            ...
        ],
        "SuggestionToAddNewTech": [
            {{
                "NewTechName": "Suggested new technology name",
                "Benefit": "Key advantages of adding this technology."
            }},
            ...
        ]
    }}

    Only return the JSON. Do not include any additional text or preamble.
    """
)
    chain_suggestion = prompt_suggestion | llm
    res = chain_suggestion.invoke(input={
        "company_desc": company_info["company_desc"],
        "technology_info": json.dumps(technology_info, indent=4),
    })

    suggestions = json.loads(res.content)
    return suggestions

def suggest_website_technologies(company_desc):
    prompt_tech_stack = PromptTemplate.from_template(
        """
    ### COMPANY DESCRIPTION:
    {company_desc}

    ### INSTRUCTION:
    Based on the company's description, suggest a complete technology stack to build a website from scratch. The stack should include recommendations for the following categories and atleast 5 suggestion in every category:
    
    1. **Frontend**: Recommend the best technologies for the frontend, including frameworks, languages, and libraries.
    2. **Backend**: Recommend suitable backend technologies for server-side logic, APIs, and other necessary services.
    3. **Database**: Suggest appropriate database technologies (SQL/NoSQL) for data storage.
    4. **Hosting**: Recommend cloud platforms or hosting services for the website deployment.
    5. **Other Technologies**: Any additional technologies that may be beneficial to support the website (e.g., security tools, caching solutions, etc.).
    
    For each category, provide a brief description of why the technology is suitable for the company, considering its industry, size, business needs, scalability, and other factors.

    Return the suggestions in the following JSON format:
    {{
        "Frontend": [
            {{
                "technology": "Technology name",
                "reason": "Why this technology is suitable for the company."
            }},
            ...
        ],
        "Backend": [
            {{
                "technology": "Technology name",
                "reason": "Why this technology is suitable for the company."
            }},
            ...
        ],
        "Database": [
            {{
                "technology": "Technology name",
                "reason": "Why this technology is suitable for the company."
            }},
            ...
        ],
        "Hosting": [
            {{
                "service": "Hosting service name",
                "reason": "Why this hosting service is suitable for the company."
            }},
            ...
        ],
        "OtherTechnologies": [
            {{
                "technology": "Technology name",
                "reason": "Why this additional technology is beneficial."
            }},
            ...
        ]
    }}

    Only return the JSON. Do not include any additional text or preamble.
    """
    )
    
    chain_tech_stack = prompt_tech_stack | llm
    res = chain_tech_stack.invoke(input={"company_desc": company_desc})

    tech_stack_suggestions = json.loads(res.content)
    return tech_stack_suggestions

def extract_base_domain(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"

@app.route('/')
def home():
    print("Home route accessed")
    return "Hello Welcome to python server"


@app.route('/company_info', methods=['POST'])
def get_company_info():
    url = request.json.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    try:
        company_info = extract_company_description(url)
        base_url = extract_base_domain(url)
        technology_info = extract_company_technology(base_url)
        # app.logger.debug(f"Response from tech info: {technology_info}")
        suggestions = suggest_better_technologies(company_info, technology_info)
        tech_stack = suggest_website_technologies(company_info)
        return jsonify({
            "company_info": company_info,
            "technology_info": technology_info,
            "suggestions": suggestions,
            "New_website_stack_suggestions": tech_stack
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host="0.0.0.0", port=port)
