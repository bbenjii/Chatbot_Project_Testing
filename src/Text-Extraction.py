from bs4 import BeautifulSoup
import requests


url = "https://www.intact.ca/en/faq"
# url = "https://www.space.com/25126-big-bang-theory.html"
user_agent =  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0.1 Safari/604.3.5-741"

headers = {
    "User-Agent": user_agent
}

req = requests.get(url, headers = headers)

soup = BeautifulSoup(req.content, "html.parser")
print(soup.get_text())

# file = open("intact_knowledge_base.txt",'w')
#
# file.write(soup.get_text().replace("  ","").replace("\n\n",""))
#
#
# # print(soup.get_text())
# file.close()
