import { Stack, Button, Switch, Paper, Title, Alert, Accordion } from '@mantine/core'
import { useState } from 'react'
import { IconAlertCircle } from '@tabler/icons-react'
import { ConfigSummary } from '../review/ConfigSummary'
import { PreflightChecklist } from '../review/PreflightChecklist'
import { ProgressDisplay } from '../review/ProgressDisplay'
import { useWorkflowRunner, useUploadCsv } from '../../../api/hooks'
import { useWizard } from '../WizardContext'
import { notifications } from '@mantine/notifications'

export function ReviewExecuteStep() {
  const { state } = useWizard()
  const [runSimulation, setRunSimulation] = useState(true)
  const [copyToClipboard, setCopyToClipboard] = useState(false)
  const [sendToOpentrons, setSendToOpentrons] = useState(false)

  const workflow = useWorkflowRunner()
  const uploadCsv = useUploadCsv()

  const canExecute =
    state.deckLayout.some(l => l.type === 'source') &&
    state.deckLayout.some(l => l.type === 'destination') &&
    state.deckLayout.some(l => l.type === 'tip') &&
    state.settings !== null &&
    state.csv.content.length > 0 &&
    state.csv.filename !== ''

  const handleExecute = async () => {
    const csvName = state.csv.filename || 'wizard.csv'
    try {
      await uploadCsv.mutateAsync({ name: csvName, content: state.csv.content })
      workflow.mutate({
        csv: csvName,
        run_simulation: runSimulation,
        copy_to_clipboard: copyToClipboard,
        send_to_opentrons: sendToOpentrons,
        use_shell_runner: false
      })
    } catch (error) {
      notifications.show({
        color: 'red',
        title: 'Failed to save CSV',
        message: error instanceof Error ? error.message : 'Unable to persist CSV before execution',
        position: 'top-right'
      })
    }
  }

  return (
    <Stack gap="md">
      <ConfigSummary />
      <PreflightChecklist />

      <Paper withBorder p="md">
        <Title order={4} mb="md">Execution Options</Title>

        {!canExecute && (
          <Alert color="orange" icon={<IconAlertCircle size={16} />} mb="md">
            Cannot execute workflow. Please complete all previous steps and fix any preflight errors.
          </Alert>
        )}

        <Stack gap="sm">
          <Switch
            label="Run opentrons_simulate validation"
            description="Validate protocol using Opentrons simulator before deployment"
            checked={runSimulation}
            onChange={(e) => setRunSimulation(e.target.checked)}
          />
          <Switch
            label="Send to Opentrons deployment path"
            description="Copy protocol to configured Opentrons App directory"
            checked={sendToOpentrons}
            onChange={(e) => setSendToOpentrons(e.target.checked)}
          />

          <Accordion variant="separated">
            <Accordion.Item value="advanced">
              <Accordion.Control>Advanced Options</Accordion.Control>
              <Accordion.Panel>
                <Switch
                  label="Copy protocol to clipboard"
                  description="Automatically copy generated protocol to system clipboard"
                  checked={copyToClipboard}
                  onChange={(e) => setCopyToClipboard(e.target.checked)}
                />
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        </Stack>
      </Paper>

      <Button
        onClick={handleExecute}
        loading={workflow.isPending}
        disabled={!canExecute}
        size="lg"
        fullWidth
      >
        {workflow.isPending ? 'Running Workflow...' : 'Run Workflow'}
      </Button>

      <ProgressDisplay
        workflowData={workflow.data || null}
        isLoading={workflow.isPending}
        error={workflow.error}
      />
    </Stack>
  )
}
