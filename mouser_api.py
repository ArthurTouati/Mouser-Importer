import requests

class MouserAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.mouser.com/api/v2"

    def search_keyword(self, keyword):
        url = f"{self.base_url}/search/keyword?apiKey={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "SearchByKeywordRequest": {
                "keyword": keyword,
                "records": 50,
                "startingRecord": 0,
                "searchOptions": "",
                "searchWithYourSignUpLanguage": ""
            }
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "Errors" in data and data["Errors"]:
                raise Exception(data["Errors"][0].get("Message", "Unknown Mouser API Error"))
            
            # The API returns 'SearchResults' -> 'Parts'
            search_results = data.get("SearchResults", {})
            parts = search_results.get("Parts", [])
            return parts
        else:
            response.raise_for_status()

