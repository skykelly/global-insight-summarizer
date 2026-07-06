import OpenAI from 'openai'

let client: OpenAI | null = null

// 빌드 시점(OPENAI_API_KEY 부재)에 모듈 평가 중 인스턴스화되어
// 빌드를 실패시키지 않도록 첫 사용 시점까지 생성을 지연한다.
export function getOpenAI(): OpenAI {
  if (!client) client = new OpenAI()
  return client
}
