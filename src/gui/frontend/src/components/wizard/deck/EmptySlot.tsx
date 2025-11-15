import { Card, Text, Center, rem } from '@mantine/core'
import { useDroppable } from '@dnd-kit/core'
import { useState } from 'react'
import { LabwareModal } from './LabwareModal'

interface EmptySlotProps {
  slot: number
}

export function EmptySlot({ slot }: EmptySlotProps) {
  const [modalOpen, setModalOpen] = useState(false)
  const { setNodeRef, isOver } = useDroppable({ id: `slot-${slot}` })

  return (
    <>
      <Card
        ref={setNodeRef}
        withBorder
        radius="md"
        p="md"
        style={{
          borderStyle: 'dashed',
          borderWidth: rem(2),
          borderColor: isOver ? 'var(--mantine-color-blue-6)' : 'var(--mantine-color-gray-4)',
          backgroundColor: isOver ? 'var(--mantine-color-blue-0)' : 'var(--mantine-color-gray-0)',
          cursor: 'pointer',
          minHeight: rem(120),
          transition: 'all 0.2s ease',
        }}
        onClick={() => setModalOpen(true)}
      >
        <Center h="100%">
          <Text size="xl" c="dimmed" fw={500}>
            {slot}
          </Text>
        </Center>
      </Card>

      <LabwareModal
        key={`add-${slot}`}
        opened={modalOpen}
        onClose={() => setModalOpen(false)}
        slot={slot}
      />
    </>
  )
}
