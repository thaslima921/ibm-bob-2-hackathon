export default function ReleaseBadge({ verdict, reasons }) {
  const config = {
    GO: {
      bg: 'bg-green-50',
      border: 'border-green-300',
      text: 'text-green-700',
      badge: 'bg-green-500',
      icon: '✓',
      label: 'GO',
      subtitle: 'Based on analyzed evidence, this change appears safe to release',
    },
    CAUTION: {
      bg: 'bg-amber-50',
      border: 'border-amber-300',
      text: 'text-amber-700',
      badge: 'bg-amber-500',
      icon: '⚠',
      label: 'CAUTION',
      subtitle: 'Based on analyzed evidence, this change should be reviewed before release',
    },
    BLOCK: {
      bg: 'bg-red-50',
      border: 'border-red-300',
      text: 'text-red-700',
      badge: 'bg-red-600',
      icon: '✕',
      label: 'BLOCK',
      subtitle: 'Based on analyzed evidence, this change should not be released without remediation',
    },
  }

  const c = config[verdict] || config.CAUTION

  return (
    <div className={`rounded-xl border-2 ${c.border} ${c.bg} p-6`}>
      <div className="flex items-start gap-4">
        <div className={`${c.badge} text-white rounded-full w-16 h-16 flex items-center justify-center text-3xl font-bold shadow shrink-0`}>
          {c.icon}
        </div>
        <div>
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-0.5">
            Evidence-Based Release Risk Assessment
          </div>
          <div className={`text-3xl font-black ${c.text} tracking-wide`}>{c.label}</div>
          <div className={`text-sm ${c.text} opacity-80 mt-0.5`}>{c.subtitle}</div>
        </div>
      </div>
      {reasons && reasons.length > 0 && (
        <ul className={`mt-4 space-y-1 text-sm ${c.text}`}>
          {reasons.map((r, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="mt-0.5 shrink-0">•</span>
              <span>{r}</span>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-4 text-xs text-slate-500 italic">
        This assessment is based on static analysis of the provided diff and repository evidence.
        It does not constitute a guarantee of correctness or security.
      </p>
    </div>
  )
}
