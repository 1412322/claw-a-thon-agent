const QC_PROMPTS = [
  { label: '🧪 Viết Test Case', template: 'Viết test case đầy đủ cho tính năng: ' },
  { label: '🐛 Báo cáo Bug Jira', template: 'Tạo bug report Jira format cho lỗi sau: ' },
  { label: '📋 Happy/Negative/Edge', template: 'Liệt kê toàn bộ kịch bản Happy Path, Negative Path và Edge Case cho tính năng: ' },
  { label: '🔍 Phân tích Log lỗi', template: 'Phân tích nguyên nhân và gợi ý fix cho log lỗi sau:\n\n' },
  { label: '✅ Checklist Smoke Test', template: 'Tạo checklist Smoke Test nhanh cho tính năng: ' },
]

const DEV_PROMPTS = [
  { label: '📝 Tạo MR Template', template: 'Tạo GitLab Merge Request template cho tính năng: ' },
  { label: '💻 Viết code', template: 'Viết code cho chức năng: ' },
  { label: '🔎 Review bảo mật', template: 'Review bảo mật và coding convention cho đoạn code sau:\n\n```\n\n```' },
  { label: '🏗️ Thiết kế API', template: 'Thiết kế API endpoint cho tính năng: ' },
  { label: '🐞 Debug lỗi', template: 'Phân tích và fix lỗi sau:\n\n' },
]

export default function QuickPrompts({ role, onSelect }) {
  const prompts = role === 'qc' ? QC_PROMPTS : DEV_PROMPTS

  return (
    <div className="px-4 pb-2">
      <div className="flex flex-wrap gap-2">
        {prompts.map((p) => (
          <button
            key={p.label}
            onClick={() => onSelect(p.template)}
            className="text-xs px-3 py-1.5 rounded-full border border-slate-700 bg-slate-800/60 text-slate-300 hover:border-blue-500/60 hover:text-blue-300 hover:bg-blue-950/30 transition-all duration-150 whitespace-nowrap"
          >
            {p.label}
          </button>
        ))}
      </div>
    </div>
  )
}
