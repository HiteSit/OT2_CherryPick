import { Paper, Stack, Title, Stepper, Alert, Textarea, Text, Badge, Group } from '@mantine/core'
import { IconCheck, IconX, IconAlertCircle } from '@tabler/icons-react'
import type { WorkflowResponse } from '../../../api/types'

interface ProgressDisplayProps {
  workflowData: WorkflowResponse | null
  isLoading: boolean
  error: Error | null
}

export function ProgressDisplay({ workflowData, isLoading, error }: ProgressDisplayProps) {
  if (isLoading) {
    return (
      <Paper withBorder p="md">
        <Title order={4} mb="md">Execution Progress</Title>
        <Alert color="blue" icon={<IconAlertCircle size={16} />}>
          Running workflow... Please wait.
        </Alert>
      </Paper>
    )
  }

  if (error) {
    return (
      <Paper withBorder p="md">
        <Title order={4} mb="md">Execution Error</Title>
        <Alert color="red" icon={<IconX size={16} />}>
          <Text fw={500} mb="xs">Workflow failed</Text>
          <Text size="sm">{error.message}</Text>
        </Alert>
      </Paper>
    )
  }

  if (!workflowData) {
    return null
  }

  const hasSimulation = workflowData.simulation !== null && workflowData.simulation !== undefined
  const simulationSuccess = hasSimulation && workflowData.simulation?.success
  const hasDeployment = workflowData.deployment !== null
  const isSuccess = workflowData.generated && (!hasSimulation || simulationSuccess)

  // Determine active step
  let activeStep = 0
  if (workflowData.generated) activeStep = 1
  if (hasSimulation) activeStep = 2
  if (hasDeployment || isSuccess) activeStep = 3

  return (
    <Paper withBorder p="md">
      <Title order={4} mb="md">Execution Results</Title>

      <Stepper active={activeStep} size="sm">
        <Stepper.Step
          label="Generate"
          description="Protocol file"
          icon={workflowData.generated ? <IconCheck size={16} /> : undefined}
        >
          {workflowData.generated && (
            <Stack gap="xs" mt="md">
              <Group gap="xs">
                <Badge color="green">Generated</Badge>
                <Text size="sm">{workflowData.generated.protocol_file}</Text>
              </Group>
              <Text size="xs" c="dimmed">
                JSON config size: {workflowData.generated.json_size} bytes
              </Text>
            </Stack>
          )}
        </Stepper.Step>

        <Stepper.Step
          label="Simulate"
          description="Validate protocol"
          icon={simulationSuccess ? <IconCheck size={16} /> : hasSimulation ? <IconX size={16} /> : undefined}
          color={simulationSuccess ? 'green' : hasSimulation ? 'red' : undefined}
        >
          {hasSimulation && (
            <Stack gap="xs" mt="md">
              {simulationSuccess ? (
                <Badge color="green">Simulation Passed</Badge>
              ) : (
                <Badge color="red">Simulation Failed</Badge>
              )}
            </Stack>
          )}
        </Stepper.Step>

        <Stepper.Step
          label="Deploy"
          description="Copy to destination"
          icon={hasDeployment ? <IconCheck size={16} /> : undefined}
        >
          {hasDeployment && workflowData.deployment && (
            <Stack gap="xs" mt="md">
              <Badge color="green">Deployed</Badge>
              {workflowData.deployment.copies.length > 0 && (
                <Text size="xs" c="dimmed">
                  Copied to: {workflowData.deployment.copies.join(', ')}
                </Text>
              )}
              {workflowData.deployment.clipboard && (
                <Text size="xs" c="dimmed">
                  ✓ Copied to clipboard
                </Text>
              )}
            </Stack>
          )}
        </Stepper.Step>
      </Stepper>

      {isSuccess && !hasSimulation && (
        <Alert color="green" icon={<IconCheck size={16} />} mt="md">
          Protocol generated successfully! (Simulation skipped)
        </Alert>
      )}

      {isSuccess && simulationSuccess && (
        <Alert color="green" icon={<IconCheck size={16} />} mt="md">
          Protocol generated and validated successfully!
        </Alert>
      )}

      {hasSimulation && !simulationSuccess && (
        <Alert color="red" icon={<IconX size={16} />} mt="md">
          Simulation failed. Check output below for details.
        </Alert>
      )}

      {hasSimulation && workflowData.simulation && (
        <Stack mt="md" gap="xs">
          {workflowData.simulation.stdout && (
            <Textarea
              label="Simulation Output"
              value={workflowData.simulation.stdout}
              readOnly
              minRows={15}
              maxRows={30}
              styles={{ input: { fontFamily: 'monospace', fontSize: '0.75rem' } }}
            />
          )}
          {workflowData.simulation.stderr && (
            <Textarea
              label="Simulation Errors"
              value={workflowData.simulation.stderr}
              readOnly
              minRows={10}
              maxRows={20}
              styles={{ input: { fontFamily: 'monospace', fontSize: '0.75rem', color: 'var(--mantine-color-red-6)' } }}
            />
          )}
        </Stack>
      )}

      {workflowData.logs && workflowData.logs.length > 0 && (
        <Stack mt="md" gap="xs">
          <Text size="sm" fw={500}>Execution Logs:</Text>
          {workflowData.logs.map((log, i) => (
            <Text key={i} size="xs" c="dimmed" style={{ fontFamily: 'monospace' }}>
              {log}
            </Text>
          ))}
        </Stack>
      )}
    </Paper>
  )
}
