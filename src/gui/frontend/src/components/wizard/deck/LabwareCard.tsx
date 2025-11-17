import { Card, Badge, Text, Group, ActionIcon, Tooltip, Stack, rem } from '@mantine/core'
import { IconEdit, IconTrash, IconGripVertical } from '@tabler/icons-react'
import { useDraggable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import type { WorkingPlateEntry } from '../../../api/types'
import { useState } from 'react'
import { LabwareModal } from './LabwareModal'
import { useWizard } from '../WizardContext'
import { usePatchSetting } from '../../../api/hooks'

interface LabwareCardProps {
  labware: WorkingPlateEntry
  slot: number
}

const TYPE_COLORS: Record<string, string> = {
  source: 'blue',
  destination: 'green',
  tip: 'yellow',
  module: 'grape',
  reservoir: 'cyan',
}

export function LabwareCard({ labware, slot }: LabwareCardProps) {
  const [editModalOpen, setEditModalOpen] = useState(false)
  const { state, setDeckLayout } = useWizard()
  const patchSettings = usePatchSetting()

  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: `labware-${slot}`,
  })

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.5 : 1,
    cursor: isDragging ? 'grabbing' : 'grab',
    minHeight: rem(140),
    height: '100%',
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    const updatedLayout = state.deckLayout.filter(l => l.position_rack !== String(slot))
    setDeckLayout(updatedLayout)
    patchSettings.mutate({ path: 'settings.working_plate', value: updatedLayout })
  }

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditModalOpen(true)
  }

  return (
    <>
      <Card
        ref={setNodeRef}
        {...attributes}
        withBorder
        radius="md"
        p="sm"
        style={style}
      >
        <Stack gap="xs">
          <Group justify="space-between">
            <Badge color={TYPE_COLORS[labware.type] || 'gray'} size="sm">
              {labware.type}
            </Badge>
            <div {...listeners} style={{ cursor: 'grab', display: 'flex', alignItems: 'center' }}>
              <IconGripVertical size={16} color="var(--mantine-color-gray-6)" />
            </div>
          </Group>

          <Tooltip
            label={`Category: ${labware.type} | Slot: ${slot}`}
            multiline
            maw={300}
          >
            <Text size="sm" fw={500} lineClamp={2}>
              {labware.labware_id || 'Unknown Labware'}
            </Text>
          </Tooltip>

          {labware.connection && (
            <Text size="xs" c="dimmed">
              Connected: {labware.connection}
            </Text>
          )}

          {labware.module_type && (
            <Text size="xs" c="dimmed">
              Module: {labware.module_type}
            </Text>
          )}

          <Group justify="flex-end" gap="xs">
            <ActionIcon
              size="sm"
              variant="subtle"
              color="blue"
              onClick={handleEdit}
              aria-label="Edit labware"
            >
              <IconEdit size={14} />
            </ActionIcon>
            <ActionIcon
              size="sm"
              variant="subtle"
              color="red"
              onClick={handleDelete}
              aria-label="Delete labware"
            >
              <IconTrash size={14} />
            </ActionIcon>
          </Group>
        </Stack>
      </Card>

      <LabwareModal
        opened={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        slot={slot}
        existingLabware={labware}
      />
    </>
  )
}
