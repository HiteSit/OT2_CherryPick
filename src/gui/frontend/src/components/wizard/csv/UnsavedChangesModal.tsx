import { Modal, Button, Group, Text, Stack } from '@mantine/core'
import { IconAlertTriangle } from '@tabler/icons-react'

interface UnsavedChangesModalProps {
  opened: boolean
  onDiscard: () => void
  onCancel: () => void
  targetFile: string
}

export function UnsavedChangesModal({ opened, onDiscard, onCancel, targetFile }: UnsavedChangesModalProps) {
  return (
    <Modal
      opened={opened}
      onClose={onCancel}
      title="Unsaved Changes"
      centered
    >
      <Stack gap="md">
        <Group gap="sm">
          <IconAlertTriangle size={24} color="var(--mantine-color-yellow-6)" />
          <Text>You have unsaved changes that will be lost.</Text>
        </Group>
        <Text size="sm" c="dimmed">
          Switching to "{targetFile}" will discard your current edits.
        </Text>
        <Group justify="flex-end" gap="sm">
          <Button variant="default" onClick={onCancel}>
            Cancel
          </Button>
          <Button color="red" onClick={onDiscard}>
            Discard
          </Button>
        </Group>
      </Stack>
    </Modal>
  )
}
