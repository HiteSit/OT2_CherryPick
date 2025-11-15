import { Stack, Button, Switch, Paper, Title, Text, Alert, TextInput, Group } from '@mantine/core'
import { useState, useEffect } from 'react'
import { IconAlertCircle } from '@tabler/icons-react'
import { ConfigSummary } from '../review/ConfigSummary'
import { PreflightChecklist } from '../review/PreflightChecklist'
import { ProgressDisplay } from '../review/ProgressDisplay'
import { useWorkflowRunner, useShellSettingsQuery, useUpdateShellSettings, useBrowseShellSettings } from '../../../api/hooks'
import { useWizard } from '../WizardContext'

export function ReviewExecuteStep() {
  const { state } = useWizard()
  const [runSimulation, setRunSimulation] = useState(true)
  const [copyToClipboard, setCopyToClipboard] = useState(false)
  const [sendToOpentrons, setSendToOpentrons] = useState(false)

  const workflow = useWorkflowRunner()
  const { data: shellSettings } = useShellSettingsQuery()
  const updateShellSettings = useUpdateShellSettings()
  const browseFolder = useBrowseShellSettings()

  const [labwarePath, setLabwarePath] = useState('')
  const [protocolPath, setProtocolPath] = useState('')

  // Initialize paths from shell settings
  useEffect(() => {
    if (shellSettings) {
      setLabwarePath(shellSettings.labware_path_win || '')
      setProtocolPath(shellSettings.target_protocol_src_win || '')
    }
  }, [shellSettings])

  const canExecute =
    state.deckLayout.some(l => l.type === 'source') &&
    state.deckLayout.some(l => l.type === 'destination') &&
    state.deckLayout.some(l => l.type === 'tip') &&
    state.settings !== null &&
    state.csv.content.length > 0 &&
    state.csv.filename !== ''

  const handleBrowseLabware = async () => {
    const result = await browseFolder.mutateAsync('labware_path_win')
    if (result) setLabwarePath(result)
  }

  const handleBrowseProtocol = async () => {
    const result = await browseFolder.mutateAsync('target_protocol_src_win')
    if (result) setProtocolPath(result)
  }

  const handleSavePaths = () => {
    updateShellSettings.mutate({
      labware_path_win: labwarePath,
      target_protocol_src_win: protocolPath
    })
  }

  const handleExecute = () => {
    workflow.mutate({
      csv: state.csv.filename,
      run_simulation: runSimulation,
      copy_to_clipboard: copyToClipboard,
      send_to_opentrons: sendToOpentrons,
      use_shell_runner: false
    })
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
            label="Copy protocol to clipboard"
            description="Automatically copy generated protocol to system clipboard"
            checked={copyToClipboard}
            onChange={(e) => setCopyToClipboard(e.target.checked)}
          />
          <Switch
            label="Send to Opentrons deployment path"
            description="Copy protocol to configured Opentrons App directory"
            checked={sendToOpentrons}
            onChange={(e) => setSendToOpentrons(e.target.checked)}
          />
        </Stack>
      </Paper>

      {sendToOpentrons && (
        <Paper withBorder p="md">
          <Title order={5} mb="md">Shell Runner Windows Folders</Title>
          <Text size="sm" c="dimmed" mb="md">
            Configure Windows paths for simulation and deployment. These paths are required when "Send to Opentrons" is enabled.
          </Text>
          <Stack gap="md">
            <div>
              <TextInput
                label="Custom labware folder (Windows)"
                placeholder="C:\Users\...\AppData\Roaming\Opentrons\labware"
                description="Path to Opentrons custom labware JSON files (required for simulation)"
                value={labwarePath}
                onChange={(e) => setLabwarePath(e.target.value)}
              />
              <Group mt="xs">
                <Button
                  size="xs"
                  variant="light"
                  onClick={handleBrowseLabware}
                  loading={browseFolder.isPending}
                >
                  Browse...
                </Button>
              </Group>
            </div>

            <div>
              <TextInput
                label="Opentrons protocol folder (Windows)"
                placeholder="C:\Users\...\AppData\Roaming\Opentrons\protocols\{UUID}\src"
                description="Path to target Opentrons App protocol directory (must end with \src)"
                value={protocolPath}
                onChange={(e) => setProtocolPath(e.target.value)}
              />
              <Group mt="xs">
                <Button
                  size="xs"
                  variant="light"
                  onClick={handleBrowseProtocol}
                  loading={browseFolder.isPending}
                >
                  Browse...
                </Button>
              </Group>
            </div>

            <Button
              onClick={handleSavePaths}
              variant="filled"
              loading={updateShellSettings.isPending}
              disabled={!labwarePath && !protocolPath}
            >
              Save as default
            </Button>
          </Stack>
        </Paper>
      )}

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
