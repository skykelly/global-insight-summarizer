export interface DiffLine {
  type: 'equal' | 'add' | 'remove'
  text: string
}

// 줄 단위 LCS 기반 diff.
export function diffLines(oldText: string, newText: string): DiffLine[] {
  const oldLines = oldText.split('\n')
  const newLines = newText.split('\n')
  const m = oldLines.length
  const n = newLines.length

  const lcs: number[][] = Array.from({ length: m + 1 }, () => new Array<number>(n + 1).fill(0))
  for (let i = m - 1; i >= 0; i--) {
    for (let j = n - 1; j >= 0; j--) {
      lcs[i][j] = oldLines[i] === newLines[j]
        ? lcs[i + 1][j + 1] + 1
        : Math.max(lcs[i + 1][j], lcs[i][j + 1])
    }
  }

  const result: DiffLine[] = []
  let i = 0
  let j = 0
  while (i < m && j < n) {
    if (oldLines[i] === newLines[j]) {
      result.push({ type: 'equal', text: oldLines[i] })
      i++; j++
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      result.push({ type: 'remove', text: oldLines[i] })
      i++
    } else {
      result.push({ type: 'add', text: newLines[j] })
      j++
    }
  }
  while (i < m) { result.push({ type: 'remove', text: oldLines[i] }); i++ }
  while (j < n) { result.push({ type: 'add', text: newLines[j] }); j++ }

  return result
}
