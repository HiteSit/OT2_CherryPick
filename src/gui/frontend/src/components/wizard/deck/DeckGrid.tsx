import { SimpleGrid, Stack, Title } from '@mantine/core'
import { DndContext, PointerSensor, useSensor, useSensors } from '@dnd-kit/core'
import type { DragEndEvent } from '@dnd-kit/core'
import { EmptySlot } from './EmptySlot'
import { LabwareCard } from './LabwareCard'
import { useWizard } from '../WizardContext'
import { usePatchSetting } from '../../../api/hooks'

export function DeckGrid() {
  const { state, setDeckLayout } = useWizard()
  const patchSettings = usePatchSetting()

  // OT-2 deck slots in visual order (top to bottom, left to right)
  const slots = [10, 11, 12, 7, 8, 9, 4, 5, 6, 1, 2, 3]

  // Configure pointer sensor with distance threshold to prevent accidental drags
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  )

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (!over) return

    // Extract slot numbers from IDs
    const activeId = String(active.id)
    const overId = String(over.id)

    // Get source and target slots
    const fromSlotMatch = activeId.match(/labware-(\d+)/)
    const toSlotMatch = overId.match(/slot-(\d+)/)

    if (!fromSlotMatch || !toSlotMatch) return

    const fromSlot = fromSlotMatch[1]
    const toSlot = toSlotMatch[1]

    if (fromSlot === toSlot) return

    // Find the labware being moved
    const labwareIndex = state.deckLayout.findIndex(
      l => l.position_rack === fromSlot
    )

    if (labwareIndex === -1) return

    // Check if target slot is occupied
    const targetOccupied = state.deckLayout.some(
      l => l.position_rack === toSlot
    )

    if (targetOccupied) {
      // Swap labware positions
      const updatedLayout = state.deckLayout.map(item => {
        if (item.position_rack === fromSlot) {
          return { ...item, position_rack: toSlot }
        }
        if (item.position_rack === toSlot) {
          return { ...item, position_rack: fromSlot }
        }
        return item
      })
      setDeckLayout(updatedLayout)
      patchSettings.mutate({ path: 'settings.working_plate', value: updatedLayout })
    } else {
      // Move to empty slot
      const updatedLayout = state.deckLayout.map(item =>
        item.position_rack === fromSlot
          ? { ...item, position_rack: toSlot }
          : item
      )
      setDeckLayout(updatedLayout)
      patchSettings.mutate({ path: 'settings.working_plate', value: updatedLayout })
    }
  }

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <Stack gap="md">
        <Title order={3}>OT-2 Deck Layout</Title>
        <SimpleGrid
          cols={3}
          spacing="md"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '1rem'
          }}
        >
          {slots.map(slot => {
            const labware = state.deckLayout.find(
              l => l.position_rack === String(slot)
            )
            return (
          <div key={slot} style={{ height: '100%' }}>
            {labware ? (
              <LabwareCard labware={labware} slot={slot} />
            ) : (
              <EmptySlot slot={slot} />
            )}
              </div>
            )
          })}
        </SimpleGrid>
      </Stack>
    </DndContext>
  )
}
