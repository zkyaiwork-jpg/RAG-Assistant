import type { ChatSource } from '../../api/chat'

export function SourceCard({ source }: { source: ChatSource }) {
  return (
    <article className="min-w-0 flex-1 rounded-xl border border-[#dfe6f3] bg-white p-4">
      <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-on-surface-variant">来源</p>
      <div className="mt-3 space-y-2 text-xs text-on-surface">
        <p className="flex items-center gap-2"><span className="material-symbols-outlined text-[18px] text-primary">folder</span><span className="break-all">{source.folder_name || '未分配文件夹'}</span></p>
        <p className="flex items-center gap-2"><span className="material-symbols-outlined text-[18px] text-primary">description</span><span className="break-all font-semibold">{source.filename || '未知来源文件'}</span></p>
      </div>
    </article>
  )
}
