import { ReactNode, useState } from 'react'
import { Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import useOnboardingHints from '@/hooks/useOnboardingHints'

interface GuideHintProps {
  hintKey: string
  title: string
  description: string
  children?: ReactNode
  side?: 'top' | 'right' | 'bottom' | 'left'
  align?: 'start' | 'center' | 'end'
  dismissLabel?: string
  className?: string
}

export default function GuideHint({
  hintKey,
  title,
  description,
  children,
  side = 'top',
  align = 'center',
  dismissLabel = 'Got it',
  className,
}: GuideHintProps) {
  const { shouldShow, markSeen, hintsEnabled } = useOnboardingHints()
  const [open, setOpen] = useState(false)

  if (!hintsEnabled || !shouldShow(hintKey)) {
    return null
  }

  const handleDismiss = () => {
    markSeen(hintKey)
    setOpen(false)
  }

  const triggerNode = children ?? (
    <button
      type="button"
      className={cn(
        'inline-flex items-center gap-1 rounded-full border border-dashed border-primary/60 bg-primary/10 px-2 py-1 text-xs font-medium text-primary shadow-sm transition hover:bg-primary/20 focus:outline-none focus:ring-2 focus:ring-primary/50',
        className,
      )}
      onClick={() => setOpen((prev) => !prev)}
    >
      <Sparkles className="h-3 w-3" aria-hidden="true" />
      Guide
    </button>
  )

  return (
    <TooltipProvider delayDuration={0}>
      <Tooltip open={open} onOpenChange={setOpen}>
        <TooltipTrigger asChild>
          {triggerNode}
        </TooltipTrigger>
        <TooltipContent className="max-w-xs space-y-2" side={side} align={align}>
          <div className="space-y-1">
            <p className="text-sm font-semibold">{title}</p>
            <p className="text-xs text-muted-foreground">{description}</p>
          </div>
          <button
            type="button"
            className="text-xs font-medium text-primary hover:underline"
            onClick={handleDismiss}
          >
            {dismissLabel}
          </button>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}


