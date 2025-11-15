import { useCallback, useState } from 'react'

const STORAGE_KEY = 'whatslang:onboarding-hints'

type DismissedMap = Record<string, boolean>

interface HintsState {
  dismissed: DismissedMap
  enabled: boolean
}

const defaultState: HintsState = {
  dismissed: {},
  enabled: true,
}

const readStoredState = (): HintsState => {
  if (typeof window === 'undefined') {
    return defaultState
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return defaultState
    }
    const parsed = JSON.parse(raw)
    return {
      dismissed:
        parsed?.dismissed && typeof parsed.dismissed === 'object'
          ? parsed.dismissed
          : {},
      enabled:
        typeof parsed?.enabled === 'boolean' ? parsed.enabled : defaultState.enabled,
    }
  } catch {
    return defaultState
  }
}

const persistState = (state: HintsState) => {
  if (typeof window === 'undefined') {
    return
  }
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    // Ignore persistence failures
  }
}

const useOnboardingHints = () => {
  const [state, setState] = useState<HintsState>(() => readStoredState())

  const updateState = useCallback((updater: (prev: HintsState) => HintsState) => {
    setState((prev) => {
      const next = updater(prev)
      persistState(next)
      return next
    })
  }, [])

  const shouldShow = useCallback(
    (key: string) => state.enabled && !state.dismissed[key],
    [state],
  )

  const markSeen = useCallback(
    (key: string) => {
      updateState((prev) => {
        if (prev.dismissed[key]) {
          return prev
        }
        return {
          ...prev,
          dismissed: { ...prev.dismissed, [key]: true },
        }
      })
    },
    [updateState],
  )

  const resetHint = useCallback(
    (key: string) => {
      updateState((prev) => {
        if (!prev.dismissed[key]) {
          return prev
        }
        const nextDismissed = { ...prev.dismissed }
        delete nextDismissed[key]
        return {
          ...prev,
          dismissed: nextDismissed,
        }
      })
    },
    [updateState],
  )

  const resetAllHints = useCallback(() => {
    updateState((prev) => ({
      ...prev,
      dismissed: {},
    }))
  }, [updateState])

  const setHintsEnabled = useCallback(
    (enabled: boolean) => {
      updateState((prev) => {
        if (prev.enabled === enabled) {
          return prev
        }
        return {
          ...prev,
          enabled,
        }
      })
    },
    [updateState],
  )

  return {
    shouldShow,
    markSeen,
    resetHint,
    resetAllHints,
    setHintsEnabled,
    hintsEnabled: state.enabled,
    dismissedHints: state.dismissed,
  }
}

export default useOnboardingHints


