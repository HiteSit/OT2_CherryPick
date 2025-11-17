import { useEffect } from 'react'
import { Stepper, Container, Box } from '@mantine/core'
import { WizardProvider, useWizard } from './WizardContext'
import { WizardNavigation } from './WizardNavigation'
import { DeckSetupStep } from './steps/DeckSetupStep'
import { ConfigurationStep } from './steps/ConfigurationStep'
import { TransferMapStep } from './steps/TransferMapStep'
import { ReviewExecuteStep } from './steps/ReviewExecuteStep'
import { useSettingsQuery } from '../../api/hooks'

export function ProtocolWizard() {
  return (
    <WizardProvider>
      <WizardContent />
    </WizardProvider>
  )
}

function WizardContent() {
  const { state, setCurrentStep, setDeckLayout, setSettings } = useWizard()
  const { data: settings } = useSettingsQuery()

  // Keep wizard state in sync with backend settings (including deck layout)
  // Note: setSettings and setDeckLayout are stable Context functions and should NOT be in the dependency array
  // Including them causes infinite loops because they get new references on every parent render
  useEffect(() => {
    if (settings) {
      setSettings(settings)
      setDeckLayout(settings.settings?.working_plate ?? [])
    }
  }, [settings])

  return (
    <Container size="xl" py="xl">
      <Stepper
        active={state.currentStep}
        onStepClick={setCurrentStep}
        allowNextStepsSelect={false}
      >
        <Stepper.Step
          label="Deck Setup"
          description="Configure labware layout"
        >
          <Box mt="xl">
            <DeckSetupStep />
          </Box>
        </Stepper.Step>

        <Stepper.Step
          label="Configuration"
          description="Protocol settings"
        >
          <Box mt="xl">
            <ConfigurationStep />
          </Box>
        </Stepper.Step>

        <Stepper.Step
          label="Transfer Map"
          description="Define transfers"
        >
          <Box mt="xl">
            <TransferMapStep />
          </Box>
        </Stepper.Step>

        <Stepper.Step
          label="Review & Execute"
          description="Run protocol"
        >
          <Box mt="xl">
            <ReviewExecuteStep />
          </Box>
        </Stepper.Step>
      </Stepper>

      <WizardNavigation />
    </Container>
  )
}
