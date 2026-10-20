import { cleanKnowledgeContent } from '../../utils/knowledgeContent'

export type SearchResult = {
  id: string
  filename: string | null
  folderName: string | null
  fileType: string | null
  chunkIndex: number | null
  distance: number | null
  content: string
  metadata: Record<string, unknown> | null
  embeddingModel: string | null
  vectorDatabase: string | null
}

export function SearchResultCard({ result }: { result: SearchResult }) {
  const isPdf = result.filename?.toLowerCase().endsWith('.pdf') ?? false
  const displayContent = cleanKnowledgeContent(result.content)

  return (
    <article className="rounded-2xl border border-white bg-white p-5 shadow-ambient transition-colors hover:border-blue-100 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
        <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${isPdf ? 'bg-rose-50 text-rose-600' : 'bg-blue-50 text-primary'}`}>
          <span className="material-symbols-outlined text-[22px]">{isPdf ? 'picture_as_pdf' : 'description'}</span>
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h3 className="break-all text-base font-semibold text-on-surface">{result.filename || '未知来源文件'}</h3>
              <div className="mt-3 rounded-xl bg-blue-50/70 px-3.5 py-3 text-xs text-on-surface-variant">
                <p className="font-semibold text-on-surface">来源</p>
                <div className="mt-2 flex flex-col gap-1.5 sm:flex-row sm:flex-wrap sm:gap-x-5">
                  <span className="inline-flex items-center gap-1.5"><span className="material-symbols-outlined text-[17px] text-primary">folder</span>{result.folderName || '未分配文件夹'}</span>
                  <span className="inline-flex items-center gap-1.5"><span className="material-symbols-outlined text-[17px] text-primary">description</span>{result.filename || '未知来源文件'}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 rounded-xl border border-[#e7ebf3] bg-[#f9fbff] px-4 py-3.5">
            <p className="whitespace-pre-line text-sm leading-7 text-on-surface">{displayContent || '暂无可展示的匹配文本'}</p>
          </div>
        </div>
      </div>
    </article>
  )
}
