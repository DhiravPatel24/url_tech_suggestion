import requests
import json
from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.prompts import PromptTemplate
from urllib.parse import urlparse

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

    # print("\n--- RAW RESPONSE FROM LLM ---\n")
    # print(res.content)  # Print the raw content

    company_description = {
        "name": url, 
        "company_desc": res.content.strip()
    }

    return company_description

def extract_company_technology(url):
    api_key = "d9442503-593a-46a2-9db1-2a51ff89c87d"
    url = f"https://api.builtwith.com/v21/api.json?KEY={api_key}&LOOKUP={url}"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving data from BuiltWith API: {e}")
        exit()

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

import json
from langchain_core.prompts import PromptTemplate

def suggest_better_technologies(company_info, technology_info):
    prompt_suggestion = PromptTemplate.from_template(
    """
    ### COMPANY DESCRIPTION:
    {company_desc}

    ### TECHNOLOGIES USED:
    {technology_info}

    ### INSTRUCTION:
    Based on the company description and the technologies currently being used, evaluate and categorize the technologies in three categories:

    1. **BetterReplace**: Identify at least 10 technologies that should be replaced with better alternatives. For each replacement, do the following:
       - Provide the suggested new technology with its name and version (if applicable).
       - Compare it with the current technology and explain why the suggested new technology is superior.
       - Highlight the advantages it offers to the company in terms of performance, scalability, cost-effectiveness, security, or user experience. Specifically, explain how the replacement can directly benefit the company’s website and business operations, such as:
         - Improving website speed, uptime, or responsiveness.
         - Enhancing security to protect customer data and build trust.
         - Reducing operational costs through automation or more efficient resource management.
         - Enhancing user experience to increase conversions or customer satisfaction.
         - Ensuring scalability for future growth without compromising performance.
       - Consider the industry (e.g., IT, e-commerce, healthcare) and the specific challenges the company may face.

    2. **GoodToUse**: List the technologies that are currently being used and are well-suited for the company based on its description. For each technology:
       - Explain why the technology is well-suited for the company’s needs.
       - Identify any key strengths it brings to the company’s operations or growth.

    3. **SuggestionToAddNewTech**: Suggest new technologies that the company is not currently using but could significantly benefit from. For each suggestion, do the following:
       - Provide the name of the new technology.
       - Explain its benefits, including how it can improve processes, productivity, or competitiveness.
       - Suggest how the technology can be integrated into the company’s existing tech stack.
       - If relevant, consider emerging technologies (e.g., AI, blockchain, 5G) that could bring a competitive advantage.

    Return the suggestions in the following JSON format:
    {{
        "BetterReplace": [
            {{
                "technology": "Suggested technology name and version",
                "comparison": "Current technology: Current technology name and version",
                "benefits": "Key advantages of switching to the suggested technology (e.g., reducing website load time by 30%, improving security with encryption protocols, cutting operational costs by 20%, what benifit to my bussiness)."
            }},
            ...
        ],
        "GoodToUse": [
            {{
                "technology": "Technology name",
                "explanation": "Why this technology is a good fit for the company."
            }},
            ...
        ],
        "SuggestionToAddNewTech": [
            {{
                "NewTechName": "Suggested new technology name",
                "Benefit": "Key advantages of adding this technology (e.g., improving user experience, enabling growth, enhancing security)."
            }},
            ...
        ]
    }}

    Only return the JSON output. Avoid including any additional text, preamble, or unnecessary formatting.
    """
)
    chain_suggestion = prompt_suggestion | llm
    res = chain_suggestion.invoke(input={
        "company_desc": company_info["company_desc"],
        "technology_info": json.dumps(technology_info, indent=4),
    })
    output_file_path = "suggested_technologies.json"
    with open(output_file_path, "w") as json_file:
        json_file.write(res.content)

    print(f"Suggestions saved to {output_file_path}")
def extract_base_domain(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"

def display_company_and_technology_info(url):
    company_info = extract_company_description(url)
    base_url = extract_base_domain(url)
    technology_info = extract_company_technology(base_url)

    # print("\n--- Company Information ---\n")
    # print(json.dumps(company_info, indent=4))

    # print("\n--- Technology Information ---\n")
    # print(json.dumps(technology_info, indent=4))

    suggestions = suggest_better_technologies(company_info, technology_info)

    print("\n--- Technology Suggestions ---\n")
    print(json.dumps(suggestions, indent=4))

if __name__ == "__main__":
    url = "https://www.iflair.com/about-iflair/"
    display_company_and_technology_info(url)







# import requests
# import json
# from langchain_groq import ChatGroq
# from langchain_community.document_loaders import WebBaseLoader
# from langchain_core.prompts import PromptTemplate
# from urllib.parse import urlparse   

# llm = ChatGroq(
#     groq_api_key="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",
#     model="llama3-8b-8192",
#     temperature=0.2,
# )

# def extract_company_description(url):
#     loader = WebBaseLoader(url)
#     page_data = loader.load().pop().page_content
#     print("\n--- RAW SCRAPED DATA ---\n")
#     prompt_extract = PromptTemplate.from_template(
#         """
#     ### SCRAPED TEXT FROM WEBSITE:
#     {page_data}
#     ### INSTRUCTION:
#     The scraped text is from the "About Us" page of a company's website. Your task is to thoroughly analyze the content and write a detailed description about the company in a professional tone. The description should:
#     - Be a minimum of 250 words.
#     - Explain what the company does, including its core services, products, and areas of expertise.
#     - Highlight the company's mission, vision, and values if mentioned.
#     - Mention key achievements, clients, or partnerships if provided in the text.
#     - Use clear, concise, and professional language.

#     Return the detailed description in a JSON format with the following keys:
#     - `name`: The company's name.
#     - `company_desc`: A 250-word detailed description of the company.

#     Only return the valid JSON.
#     please not add any line i want just json to save in new file with json open and closing tag.
#     ### VALID JSON (NO PREAMBLE):    
#     """
#     )
#     chain_extract = prompt_extract | llm
#     res = chain_extract.invoke(input={"page_data": page_data})
#     return res.content

# def extract_company_technology(url):
#     api_key = "e404d8e1-0747-4ea9-9ea3-29c3542e8175"
#     url = f"https://api.builtwith.com/v21/api.json?KEY={api_key}&LOOKUP={url}"
#     try:
#         response = requests.get(url)
#         response.raise_for_status() 
#     except requests.exceptions.RequestException as e:
#         print(f"Error retrieving data from BuiltWith API: {e}")
#         exit()

#     data = response.json()

#     if "Results" not in data or len(data["Results"]) == 0:
#         print(f"No results found for domain: {url}.")
#     else:
#         processed_data = {}
#         paths = data["Results"][0]["Result"].get("Paths", [])

#     for index, path in enumerate(paths):
#         technologies = path.get("Technologies", [])

#         if index == 0:
#             limit = 30
#         else:
#             limit = 15

#         for tech in technologies[:limit]:
#             if "Categories" in tech:
#                 category_value = ", ".join(tech["Categories"])
#                 processed_data[category_value] = tech["Name"]
#             elif "Name" in tech:
#                 processed_data[tech["Name"]] = tech["Name"]

#     filename = "processed_technologies.json"
#     with open(filename, "w") as json_file:
#         json.dump(processed_data, json_file, indent=4)
#     print(f"Processed data saved to {filename}")

#     print("Processed Data:")
#     for key, value in processed_data.items():
#         print(f"{key}: {value}")

# def extract_base_domain(url):
#     parsed_url = urlparse(url)
#     return f"{parsed_url.scheme}://{parsed_url.netloc}"



# if __name__ == "__main__":
#     url = "https://www.iflair.com/about-iflair/"
#     company_info = extract_company_description(url)

#     with open("company_description.json", "w") as f:
#         f.write(company_info)

#     base_url = extract_base_domain(url)
#     print(f"Base URL: {base_url}")
#     extract_company_technology(base_url)
