import { Stepper, Container, Box } from '@mantine/core'
import { WizardProvider, useWizard } from './WizardContext'
import { WizardNavigation } from './WizardNavigation'
import { DeckSetupStep } from './steps/DeckSetupStep'
import { ConfigurationStep } from './steps/ConfigurationStep'
import { TransferMapStep } from './steps/TransferMapStep'
import { ReviewExecuteStep } from './steps/ReviewExecuteStep'

export function ProtocolWizard() {
  return (
    <WizardProvider>
      <WizardContent />
    </WizardProvider>
  )
}

function WizardContent() {
  const { state, setCurrentStep } = useWizard()

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
