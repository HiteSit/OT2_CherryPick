import { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Group, Loader, Paper, Select, Stack, Switch, Text, Textarea, TextInput, Title } from '@mantine/core'
import { IconAlertTriangle, IconCheck, IconDeviceFloppy, IconFolder } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'
import {
  useBrowseShellSettings,
  useCsvListQuery,
  useShellSettingsQuery,
  useUpdateShellSettings,
  useWorkflowRunner,
} from '../api/hooks'
import type { ShellSettingsField } from '../api/types'

export function WorkflowRunner() {
  const csvQuery = useCsvListQuery()
  const workflow = useWorkflowRunner()
  const shellSettingsQuery = useShellSettingsQuery()
  const shellSettingsUpdate = useUpdateShellSettings()
  const shellSettingsBrowse = useBrowseShellSettings()
  const files = csvQuery.data?.files ?? []
  const [selectedCsv, setSelectedCsv] = useState<string>('')
  const [runSimulation, setRunSimulation] = useState(true)
  const [sendToOpentrons, setSendToOpentrons] = useState(false)
  const [targetPath, setTargetPath] = useState('')
  const [shellTargetPathWin, setShellTargetPathWin] = useState('')
  const [labwarePathWin, setLabwarePathWin] = useState('')
  const [activeBrowseField, setActiveBrowseField] = useState<ShellSettingsField | null>(null)
  const [activeSaveField, setActiveSaveField] = useState<ShellSettingsField | null>(null)
  const [copyToClipboard, setCopyToClipboard] = useState(false)

  useEffect(() => {
    if (shellSettingsQuery.data) {
      setShellTargetPathWin(shellSettingsQuery.data.target_protocol_src_win ?? '')
      setLabwarePathWin(shellSettingsQuery.data.labware_path_win ?? '')
    }
  }, [shellSettingsQuery.data])

  const csvOptions = useMemo(() => files.map((name) => ({ value: name, label: name })), [files])

  const handleSubmit = () => {
    if (!selectedCsv) {
      notifications.show({ color: 'red', title: 'CSV required', message: 'Select a CSV file before running.' })
      return
    }
    if (sendToOpentrons && !runSimulation && !targetPath) {
      notifications.show({ color: 'red', title: 'Target path required', message: 'Provide a target path for deployment.' })
      return
    }
    workflow.mutate(
      {
        csv: selectedCsv,
        run_simulation: runSimulation,
        use_shell_runner: runSimulation,
        send_to_opentrons: sendToOpentrons,
        target_path: sendToOpentrons && !runSimulation ? targetPath : undefined,
        copy_to_clipboard: copyToClipboard,
      },
      {
        onSuccess: () =>
          notifications.show({
            color: 'teal',
            title: 'Workflow complete',
            message: 'CherryPick_OT2.py updated successfully.',
          }),
        onError: (error) =>
          notifications.show({
            color: 'red',
            title: 'Workflow failed',
            message: error instanceof Error ? error.message : 'Unknown error.',
          }),
      },
    )
  }

  const handleBrowseShellPath = (field: ShellSettingsField) => {
    setActiveBrowseField(field)
    shellSettingsBrowse.mutate(
      { field },
      {
        onSuccess: (data) => {
          setShellTargetPathWin(data.target_protocol_src_win ?? '')
          setLabwarePathWin(data.labware_path_win ?? '')
          const message = field === 'target_protocol_src_win' ? 'Deployment folder updated.' : 'Labware folder updated.'
          notifications.show({ color: 'teal', title: 'Folder selected', message })
        },
        onError: (error) =>
          notifications.show({
            color: 'red',
            title: 'Browse failed',
            message: error instanceof Error ? error.message : 'Unable to open folder picker.',
          }),
        onSettled: () => setActiveBrowseField(null),
      },
    )
  }

  const handleSaveShellPath = (field: ShellSettingsField, value: string) => {
    if (!value) {
      notifications.show({ color: 'red', title: 'Folder required', message: 'Choose a folder before saving.' })
      return
    }
    setActiveSaveField(field)
    const payload =
      field === 'target_protocol_src_win' ? { target_protocol_src_win: value } : { labware_path_win: value }
    shellSettingsUpdate.mutate(payload, {
      onSuccess: () => {
        const title = field === 'target_protocol_src_win' ? 'Deployment path saved' : 'Labware path saved'
        notifications.show({ color: 'teal', title, message: 'Will be used for future shell runs.' })
      },
      onError: (error) =>
        notifications.show({ color: 'red', title: 'Save failed', message: error instanceof Error ? error.message : 'Unable to save folder.' }),
      onSettled: () => setActiveSaveField(null),
    })
  }

  return (
    <Stack gap="lg">
      <Stack gap="sm">
        <Title order={4}>Workflow Runner</Title>
        {csvQuery.isLoading ? (
          <Group gap="xs">
            <Loader size="sm" />
            <Text c="dimmed">Loading CSV files...</Text>
          </Group>
        ) : (
          <Select
            label="Transfer map (CSV)"
            placeholder="Select CSV"
            searchable
            data={csvOptions}
            value={selectedCsv}
            onChange={(value) => value && setSelectedCsv(value)}
          />
        )}
      </Stack>

      <Switch
        label="Run opentrons_simulate after generating protocol"
        checked={runSimulation}
        onChange={(event) => setRunSimulation(event.currentTarget.checked)}
      />

      <Switch
        label="Copy protocol to clipboard"
        checked={copyToClipboard}
        onChange={(event) => setCopyToClipboard(event.currentTarget.checked)}
      />

      <Switch
        label="Send to Opentrons deployment path"
        checked={sendToOpentrons}
        onChange={(event) => setSendToOpentrons(event.currentTarget.checked)}
      />

      {sendToOpentrons && !runSimulation && (
        <TextInput
          label="Target path"
          description="Absolute path (WSL/Unix) used when deploying without the shell runner."
          value={targetPath}
          onChange={(event) => setTargetPath(event.currentTarget.value)}
        />
      )}

      {sendToOpentrons && (
        <Paper withBorder radius="md" p="md">
          <Stack gap="sm">
            <Title order={5}>Shell runner Windows folders</Title>
            <Text size="sm" c="dimmed">
              Used when the shell runner is enabled (the default when simulation is requested).
            </Text>

            <Stack gap="xs">
            <TextInput
              label="Opentrons protocol folder (Windows)"
              description="Example: C:\\Users\\you\\AppData\\Roaming\\Opentrons\\protocols\\..."
              value={shellTargetPathWin}
              onChange={(event) => setShellTargetPathWin(event.currentTarget.value)}
            />
            <Group gap="xs">
              <Button
                variant="default"
                leftSection={<IconFolder size={16} />}
                loading={shellSettingsBrowse.isPending && activeBrowseField === 'target_protocol_src_win'}
                onClick={() => handleBrowseShellPath('target_protocol_src_win')}
              >
                Browse…
              </Button>
              <Button
                variant="light"
                leftSection={<IconDeviceFloppy size={16} />}
                loading={shellSettingsUpdate.isPending && activeSaveField === 'target_protocol_src_win'}
                onClick={() => handleSaveShellPath('target_protocol_src_win', shellTargetPathWin)}
              >
                Save as default
              </Button>
            </Group>
            </Stack>

            <Stack gap="xs">
            <TextInput
              label="Custom labware folder (Windows)"
              description="Example: C:\\Users\\you\\AppData\\Roaming\\Opentrons\\labware"
              value={labwarePathWin}
              onChange={(event) => setLabwarePathWin(event.currentTarget.value)}
            />
            <Group gap="xs">
              <Button
                variant="default"
                leftSection={<IconFolder size={16} />}
                loading={shellSettingsBrowse.isPending && activeBrowseField === 'labware_path_win'}
                onClick={() => handleBrowseShellPath('labware_path_win')}
              >
                Browse…
              </Button>
              <Button
                variant="light"
                leftSection={<IconDeviceFloppy size={16} />}
                loading={shellSettingsUpdate.isPending && activeSaveField === 'labware_path_win'}
                onClick={() => handleSaveShellPath('labware_path_win', labwarePathWin)}
              >
                Save as default
              </Button>
            </Group>
            </Stack>

            {shellSettingsQuery.isLoading && (
              <Text c="dimmed" size="sm">
                Loading saved shell settings…
              </Text>
            )}
          </Stack>
        </Paper>
      )}

      <Button loading={workflow.isPending} onClick={handleSubmit}>
        Run Workflow
      </Button>

      {workflow.data && (
        <Stack gap="md">
          <Alert variant="light" color="teal" icon={<IconCheck size={16} />}>
            <Stack gap="xs">
              <Text>
                Protocol saved to <Text span fw={700}>{workflow.data.generated.protocol_file}</Text>
              </Text>
              {workflow.data.deployment && workflow.data.deployment.copies.length > 0 && (
                <Text>
                  Deployed copies:
                  <br />
                  {workflow.data.deployment.copies.map((copy) => (
                    <Text key={copy} size="sm">
                      {copy}
                    </Text>
                  ))}
                </Text>
              )}
            </Stack>
          </Alert>

          {workflow.data.simulation && (
            <Paper withBorder radius="md" p="md">
              <Stack gap="sm">
                <Title order={5}>Simulation output</Title>
                {workflow.data.simulation.stdout && (
                  <Textarea
                    label="stdout"
                    value={workflow.data.simulation.stdout}
                    minRows={12}
                    readOnly
                    autosize
                    styles={{ input: { fontFamily: 'monospace', fontSize: '0.85rem' } }}
                  />
                )}
                {workflow.data.simulation.stderr && (
                  <Textarea
                    label="stderr"
                    value={workflow.data.simulation.stderr}
                    minRows={10}
                    readOnly
                    autosize
                    styles={{ input: { fontFamily: 'monospace', fontSize: '0.85rem' } }}
                  />
                )}
                {workflow.data.simulation.success === false && workflow.data.simulation.error && (
                  <Alert color="red" variant="light" icon={<IconAlertTriangle size={16} />}>
                    {workflow.data.simulation.error}
                  </Alert>
                )}
              </Stack>
            </Paper>
          )}

          {!!workflow.data.logs?.length && (
            <Paper withBorder radius="md" p="md">
              <Title order={5}>Log</Title>
              <Textarea
                value={workflow.data.logs.join('\n')}
                minRows={15}
                readOnly
                autosize
                styles={{ input: { fontFamily: 'monospace', fontSize: '0.85rem' } }}
              />
            </Paper>
          )}
        </Stack>
      )}

      {workflow.isError && workflow.error && (
        <Alert color="red" variant="light" icon={<IconAlertTriangle size={16} />}>
          {workflow.error instanceof Error ? workflow.error.message : 'Workflow failed.'}
        </Alert>
      )}
    </Stack>
  )
}
