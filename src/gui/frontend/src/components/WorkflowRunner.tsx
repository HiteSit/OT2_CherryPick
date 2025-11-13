import { useMemo, useState } from 'react'
import { Alert, Button, Group, Loader, Paper, Select, Stack, Switch, Text, Textarea, TextInput, Title } from '@mantine/core'
import { IconAlertTriangle, IconCheck } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'
import { useCsvListQuery, useWorkflowRunner } from '../api/hooks'

export function WorkflowRunner() {
  const csvQuery = useCsvListQuery()
  const workflow = useWorkflowRunner()
  const files = csvQuery.data?.files ?? []
  const [selectedCsv, setSelectedCsv] = useState<string>('')
  const [runSimulation, setRunSimulation] = useState(true)
  const [sendToOpentrons, setSendToOpentrons] = useState(false)
  const [targetPath, setTargetPath] = useState('')
  const [copyToClipboard, setCopyToClipboard] = useState(false)

  const csvOptions = useMemo(() => files.map((name) => ({ value: name, label: name })), [files])

  const handleSubmit = () => {
    if (!selectedCsv) {
      notifications.show({ color: 'red', title: 'CSV required', message: 'Select a CSV file before running.' })
      return
    }
    if (sendToOpentrons && !targetPath) {
      notifications.show({ color: 'red', title: 'Target path required', message: 'Provide a target path for deployment.' })
      return
    }
    workflow.mutate(
      {
        csv: selectedCsv,
        run_simulation: runSimulation,
        use_shell_runner: runSimulation,
        send_to_opentrons: sendToOpentrons,
        target_path: sendToOpentrons ? targetPath : undefined,
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

      {sendToOpentrons && (
        <TextInput
          label="Target path"
          description="Absolute path to the protocol src directory or file."
          value={targetPath}
          onChange={(event) => setTargetPath(event.currentTarget.value)}
        />
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
