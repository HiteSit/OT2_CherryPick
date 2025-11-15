import { Group, Button } from '@mantine/core'
import { useWizard } from './WizardContext'

export function WizardNavigation() {
  const { state, setCurrentStep, canProceed } = useWizard()

  const handleNext = () => {
    if (state.currentStep < 3 && canProceed(state.currentStep)) {
      setCurrentStep(state.currentStep + 1)
    }
  }

  const handleBack = () => {
    if (state.currentStep > 0) {
      setCurrentStep(state.currentStep - 1)
    }
  }

  const isLastStep = state.currentStep === 3
  const canGoNext = canProceed(state.currentStep)

  return (
    <Group justify="space-between" mt="xl">
      <Button
        variant="outline"
        onClick={handleBack}
        disabled={state.currentStep === 0}
      >
        Back
      </Button>

      <Button
        onClick={handleNext}
        disabled={isLastStep || !canGoNext}
      >
        {isLastStep ? 'Complete' : 'Next'}
      </Button>
    </Group>
  )
}
