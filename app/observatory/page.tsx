// app/observatory/page.tsx
// Antenna 이식본 — 앱의 메인. /observatory 로 접근.
// 딥링크: /observatory?nav=wiki&sector=power 처럼 초기 화면을 지정할 수 있다
// (기존 /wiki·/chat·/scoreboard 리다이렉트가 이 파라미터를 사용).
import AntennaApp from './AntennaApp';

export const metadata = { title: 'Antenna — 글로벌 리서치 인텔리전스' };

export default async function ObservatoryPage({
  searchParams,
}: {
  searchParams: Promise<{ nav?: string; sector?: string }>;
}) {
  const { nav, sector } = await searchParams;
  return <AntennaApp initialNav={nav} initialWikiSector={sector} />;
}
