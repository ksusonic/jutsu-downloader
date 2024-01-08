import asyncio

from fake_useragent import UserAgent
import tqdm.asyncio
from tqdm import tqdm
import aiohttp
import bs4


class JojoParser:
    def __init__(self, session):
        self.session = session

    @staticmethod
    def parse_jojo_content(content: str, season: int, episode: int) -> dict:
        soup = bs4.BeautifulSoup(content, 'html.parser')
        title = soup.select_one('#dle-content > div > h1 > span').contents[1]
        video_resolutions = soup.select_one('#my-player')
        best_resolution_src = video_resolutions.select_one('source:nth-child(1)')['src']
        return {
            'season': season,
            'episode': episode,
            'title': title,
            'src': best_resolution_src,
        }

    async def __download_by_url(self, url: str, title: str):
        with open(f"{title}.mp4", "wb") as fd:
            async with self.session.get(url) as resp:
                async for data in resp.content.iter_chunked(1024):
                    fd.write(data)
        return f"Downloaded: {title}"

    async def __collect_episodes(self, season: int, episodes: range) -> tuple[dict]:
        tasks = []
        for episode in episodes:
            url = f'https://jut.su/jojo-bizarre-adventure/season-{season}/episode-{episode}.html'
            tasks.append(self.__get_url_data(url, season=season, episode=episode))
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def __get_url_data(self, url: str, season: int, episode: int) -> dict:
        async with self.session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                return self.parse_jojo_content(content, season, episode)
            else:
                print(f'Error: {response.status}')
                return None

    async def download(self, season: int, episodes: range):
        episode_info_list = await self.__collect_episodes(season, episodes)
        print(f"Collected {len(episode_info_list)} episodes")

        for f in tqdm(
                [await self.__download_by_url(episode['src'], episode['title']) for episode in episode_info_list]
        ):
            print(await f)


async def main(season: int, episodes: range):
    async with aiohttp.ClientSession(headers={'User-Agent': UserAgent().random}) as session:
        await JojoParser(session).download(season, episodes)


if __name__ == '__main__':
    # ------------------
    # CHANGE PARAMS HERE
    season = 1
    episodes = range(7, 17)
    # ------------------

    asyncio.run(main(season, episodes))
