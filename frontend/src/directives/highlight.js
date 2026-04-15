import hljs from 'highlight.js/lib/core'
import cpp from 'highlight.js/lib/languages/cpp'
import 'highlight.js/styles/github.css'
import katex from 'katex'
import 'katex/dist/katex.min.css'

hljs.registerLanguage('cpp', cpp)

/**
 * Unescape HTML entities inside LaTeX math blocks.
 * KaTeX needs literal characters, not HTML-escaped ones.
 */
function unescapeHtmlInTex(tex) {
  return tex
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
}

/**
 * Render LaTeX math expressions using KaTeX:
 *   $$...$$ → display (block) math
 *   $...$ → inline math
 */
function processMath(html) {
  // Display math: $$...$$
  html = html.replace(/\$\$([\s\S]*?)\$\$/g, (_, tex) => {
    try {
      return katex.renderToString(unescapeHtmlInTex(tex.trim()), { displayMode: true, throwOnError: false })
    } catch {
      return _
    }
  })
  // Inline math: $...$  (not preceded/followed by another $)
  html = html.replace(/\$([^\$\n]+?)\$/g, (_, tex) => {
    try {
      return katex.renderToString(unescapeHtmlInTex(tex.trim()), { displayMode: false, throwOnError: false })
    } catch {
      return _
    }
  })
  return html
}

/**
 * Convert markdown-style backtick code to HTML:
 *   ```code```  or  ```cpp\ncode\n```  →  <pre><code>...</code></pre>
 *   `code`  →  <code>...</code>
 */
function processBackticks(html) {
  // Skip if already contains <pre> or <code> (already processed or hand-authored HTML)
  if (/<pre[\s>]|<code[\s>]/i.test(html)) return html

  // Triple backticks → code block (language tag only consumed if followed by newline)
  html = html.replace(/```(?:\w+\n)?([\s\S]*?)```/g, (_, code) => {
    return `<pre><code class="language-cpp">${code.trim()}</code></pre>`
  })

  // Single backticks → inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  return html
}

function processElement(el) {
  // Step 1: Render LaTeX math expressions
  const afterMath = processMath(el.innerHTML)
  if (afterMath !== el.innerHTML) {
    el.innerHTML = afterMath
  }

  // Step 2: Convert backtick syntax in text nodes
  const original = el.innerHTML
  const processed = processBackticks(original)
  if (processed !== original) {
    el.innerHTML = processed
  }

  // Step 3: Highlight <pre> blocks
  el.querySelectorAll('pre').forEach(block => {
    if (block.dataset.highlighted) return
    // If no <code> child, wrap content in one
    if (!block.querySelector('code')) {
      const code = document.createElement('code')
      code.className = 'language-cpp'
      code.innerHTML = block.innerHTML
      block.innerHTML = ''
      block.appendChild(code)
    }
    const codeEl = block.querySelector('code')
    if (codeEl && !codeEl.classList.contains('hljs')) {
      codeEl.classList.add('language-cpp')
      hljs.highlightElement(codeEl)
    }
    block.dataset.highlighted = 'true'
  })

  // Step 3: Highlight standalone <code> elements (inline code)
  el.querySelectorAll('code:not(pre code)').forEach(codeEl => {
    if (codeEl.dataset.highlighted) return
    codeEl.classList.add('inline-code')
    // Only highlight if it looks like C++ (has keywords or operators)
    const text = codeEl.textContent
    if (/\b(int|char|float|double|bool|void|string|cout|cin|for|while|if|else|return|include|using|namespace|class|struct)\b|[<>]{2}|[{};]/.test(text)) {
      codeEl.classList.add('language-cpp')
      hljs.highlightElement(codeEl)
    }
    codeEl.dataset.highlighted = 'true'
  })
}

export const vHighlight = {
  mounted(el) { processElement(el) },
  updated(el) {
    // Reset flags so new content gets processed
    el.querySelectorAll('[data-highlighted]').forEach(node => {
      delete node.dataset.highlighted
    })
    processElement(el)
  },
}
