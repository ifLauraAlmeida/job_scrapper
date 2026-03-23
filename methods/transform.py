from bs4 import BeautifulSoup


class Transform:
    def __init__(self):
        pass
    
    def soupHtml(self, html_text):
        return BeautifulSoup(html_text, "html.parser")
    
    def getJobs(self, site_source, soup):
        print(f"Minerando dados do site: {site_source}")
        match site_source:
            case "workingnomads":
                jobs_list = []
                
                # No HTML enviado, as vagas ficam dentro de links com a classe 'job-list-item'
                # ou dentro de uma div 'jobs-list'
                job_items = soup.find_all("a", class_="job_list")
                
                for item in job_items:
                    try:
                        # 1. Título: Geralmente em um <h2> ou <span> dentro do link
                        title_tag = item.find("h2") or item.find("span", class_="title")
                        title = title_tag.get_text(strip=True) if title_tag else item.get_text(strip=True)

                        # 2. Empresa: No Working Nomads, fica em um elemento com classe 'company'
                        company_tag = item.find("span", class_="company") or item.find("div", class_="company")
                        company = company_tag.get_text(strip=True) if company_tag else "Working Nomads"

                        # 3. Link: O próprio item já é o <a>
                        raw_link = item.get("href", "")
                        link = f"https://www.workingnomads.com{raw_link}" if raw_link.startswith("/") else raw_link

                        # 4. Tags: Localizadas em spans de categoria
                        tags = [t.get_text(strip=True) for t in item.find_all("span", class_="category")]
                        
                        # Evita capturar links que não sejam de vagas reais
                        jobs_list.append({
                            "title": title,
                            "company": company,
                            "link": link,
                            "tags": ", ".join(tags) if tags else "Remote"
                            })
                        print(item.find("h4"))
                    except Exception as e:
                        continue
                
                return jobs_list

            case _:
                return []