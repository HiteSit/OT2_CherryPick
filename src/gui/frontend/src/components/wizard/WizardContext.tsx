import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import type { WorkingPlateEntry, SettingsDocument } from '../../api/types'

interface WizardState {
  currentStep: number  // 0-3 (Deck Setup, Configuration, Transfer Map, Review & Execute)
  deckLayout: WorkingPlateEntry[]
  settings: SettingsDocument | null
  csv: {
    filename: string
    content: string
  }
}

interface WizardContextValue {
  state: WizardState
  setCurrentStep: (step: number) => void
  setDeckLayout: (layout: WorkingPlateEntry[]) => void
  setSettings: (settings: SettingsDocument) => void
  setCSV: (filename: string, content: string) => void
  resetWizard: () => void
  canProceed: (step: number) => boolean
}

const WizardContext = createContext<WizardContextValue | null>(null)

const initialState: WizardState = {
  currentStep: 0,
  deckLayout: [],
  settings: null,
  csv: { filename: '', content: '' }
}

export function WizardProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<WizardState>(initialState)

  const setCurrentStep = (step: number) => {
    setState(prev => ({ ...prev, currentStep: step }))
  }

  const setDeckLayout = (layout: WorkingPlateEntry[]) => {
    setState(prev => ({ ...prev, deckLayout: layout }))
  }

  const setSettings = (settings: SettingsDocument) => {
    setState(prev => ({ ...prev, settings }))
  }

  const setCSV = (filename: string, content: string) => {
    setState(prev => ({ ...prev, csv: { filename, content } }))
  }

  const resetWizard = () => {
    setState(initialState)
  }

  // Validation logic for proceeding to next step
  const canProceed = (step: number): boolean => {
    switch (step) {
      case 0: // Deck Setup -> Configuration
        // Require at least 1 source, 1 destination, and 1 tip rack
        const hasSource = state.deckLayout.some(l => l.type === 'source')
        const hasDestination = state.deckLayout.some(l => l.type === 'destination')
        const hasTip = state.deckLayout.some(l => l.type === 'tip')
        return hasSource && hasDestination && hasTip
      case 1: // Configuration -> Transfer Map
        return state.settings !== null
      case 2: // Transfer Map -> Review & Execute
        return state.csv.filename !== '' && state.csv.content !== ''
      case 3: // Review & Execute (final step)
        return true
      default:
        return false
    }
  }

  const value: WizardContextValue = {
    state,
    setCurrentStep,
    setDeckLayout,
    setSettings,
    setCSV,
    resetWizard,
    canProceed
  }

  return (
    <WizardContext.Provider value={value}>
      {children}
    </WizardContext.Provider>
  )
}

export function useWizard() {
  const context = useContext(WizardContext)
  if (!context) {
    throw new Error('useWizard must be used within WizardProvider')
  }
  return context
}
