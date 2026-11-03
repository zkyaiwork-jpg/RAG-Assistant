// 极简 Markdown 渲染：把大模型返回的 Markdown 变成安全的 HTML。
//
// 为什么手写而不是引第三方库：
// 1. 只需要标题、列表、粗体、行内代码、代码块这几种语法，一个库太重；
// 2. 先转义 HTML 再做替换，天然防 XSS —— 模型输出属于不可信内容，
//    绝对不能直接塞进 innerHTML。

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function inline(text) {
  return text
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
}

export function renderMarkdown(source) {
  if (!source) return ''
  const lines = escapeHtml(String(source)).split(/\r?\n/)
  const html = []
  let listType = null
  let inCode = false
  let codeBuffer = []

  const closeList = () => {
    if (listType) {
      html.push(`</${listType}>`)
      listType = null
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trimEnd()

    // 代码块围栏
    if (line.trim().startsWith('```')) {
      if (inCode) {
        html.push(`<pre><code>${codeBuffer.join('\n')}</code></pre>`)
        codeBuffer = []
        inCode = false
      } else {
        closeList()
        inCode = true
      }
      continue
    }

    if (inCode) {
      codeBuffer.push(rawLine)
      continue
    }

    if (!line.trim()) {
      closeList()
      continue
    }

    const heading = line.match(/^(#{1,4})\s+(.*)$/)
    if (heading) {
      closeList()
      const level = Math.min(heading[1].length, 3)
      html.push(`<h${level}>${inline(heading[2])}</h${level}>`)
      continue
    }

    const unordered = line.match(/^\s*[-*+]\s+(.*)$/)
    if (unordered) {
      if (listType !== 'ul') {
        closeList()
        html.push('<ul>')
        listType = 'ul'
      }
      html.push(`<li>${inline(unordered[1])}</li>`)
      continue
    }

    const ordered = line.match(/^\s*\d+[.)]\s+(.*)$/)
    if (ordered) {
      if (listType !== 'ol') {
        closeList()
        html.push('<ol>')
        listType = 'ol'
      }
      html.push(`<li>${inline(ordered[1])}</li>`)
      continue
    }

    const quote = line.match(/^&gt;\s?(.*)$/)
    if (quote) {
      closeList()
      html.push(`<blockquote>${inline(quote[1])}</blockquote>`)
      continue
    }

    closeList()
    html.push(`<p>${inline(line)}</p>`)
  }

  if (inCode && codeBuffer.length) {
    html.push(`<pre><code>${codeBuffer.join('\n')}</code></pre>`)
  }
  closeList()
  return html.join('')
}
