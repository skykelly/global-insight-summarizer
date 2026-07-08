// app/observatory/page.tsx
// Antenna 프로토타입 이식본을 서빙하는 라우트. /observatory 로 접근.
// AntennaApp은 순수 React 클라이언트 컴포넌트 — 이 파일은 마운트 래퍼일 뿐이다.
import AntennaApp from './AntennaApp';

export const metadata = { title: 'Antenna — 글로벌 리서치 인텔리전스' };

export default function ObservatoryPage() {
  return <AntennaApp />;
}
