import { useState } from 'react'
import {
  Accordion,
  ActionIcon,
  Badge,
  Button,
  Group,
  Modal,
  NumberInput,
  Paper,
  Select,
  Stack,
  TagsInput,
  Text,
  TextInput,
  Title,
  Tooltip,
} from '@mantine/core'
import { IconEdit, IconPlus, IconTrash } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'
import {
  useLabwareQuery,
  useAddPipetteEntry,
  useUpdatePipetteEntry,
  useDeletePipetteEntry,
} from '../../../api/hooks'
import type { PipetteEntry } from '../../../api/types'

// --- Pipette Form Modal ---

interface PipetteFormProps {
  opened: boolean
  onClose: () => void
  initial?: PipetteEntry
  editIndex?: number
}

function PipetteFormModal({ opened, onClose, initial, editIndex }: PipetteFormProps) {
  const addMutation = useAddPipetteEntry()
  const updateMutation = useUpdatePipetteEntry()

  const [name, setName] = useState(initial?.name ?? '')
  const [opentrons_id, setOpentrons_id] = useState(initial?.opentrons_id ?? '')
  const [channels, setChannels] = useState<number>(initial?.channels ?? 1)
  const [volMin, setVolMin] = useState<number>(initial?.volume_range?.[0] ?? 20)
  const [volMax, setVolMax] = useState<number>(initial?.volume_range?.[1] ?? 300)
  const [preferred_mount, setPreferred_mount] = useState<string>(initial?.preferred_mount ?? 'right')
  const [tip_connections, setTip_connections] = useState<string[]>(initial?.tip_connections ?? [])

  const isEdit = editIndex !== undefined

  const handleSubmit = () => {
    if (!name || !opentrons_id) {
      notifications.show({ color: 'red', message: 'Name and Opentrons ID are required', position: 'top-right' })
      return
    }
    const payload: PipetteEntry = {
      name,
      opentrons_id,
      channels,
      volume_range: [volMin, volMax],
      preferred_mount: preferred_mount as 'left' | 'right',
      tip_connections,
    }
    const mutation = isEdit
      ? updateMutation.mutateAsync({ index: editIndex, payload })
      : addMutation.mutateAsync(payload)

    mutation.then(() => {
      notifications.show({ color: 'teal', message: isEdit ? 'Pipette updated' : 'Pipette added', position: 'top-right' })
      onClose()
    }).catch((err: unknown) => {
      notifications.show({ color: 'red', title: 'Error', message: err instanceof Error ? err.message : 'Unknown error', position: 'top-right' })
    })
  }

  return (
    <Modal opened={opened} onClose={onClose} title={isEdit ? 'Edit Pipette' : 'Add Pipette'} size="md">
      <Stack gap="sm">
        <TextInput label="Name" placeholder="Pipette_1" value={name} onChange={(e) => setName(e.target.value)} required />
        <TextInput label="Opentrons ID" placeholder="p1000_single_gen2" value={opentrons_id} onChange={(e) => setOpentrons_id(e.target.value)} required />
        <Select
          label="Channels"
          data={[
            { value: '1', label: '1 (Single)' },
            { value: '8', label: '8 (Multi)' },
          ]}
          value={String(channels)}
          onChange={(v) => setChannels(Number(v))}
        />
        <Group grow>
          <NumberInput label="Min Volume (uL)" value={volMin} onChange={(v) => setVolMin(Number(v))} min={1} />
          <NumberInput label="Max Volume (uL)" value={volMax} onChange={(v) => setVolMax(Number(v))} min={1} />
        </Group>
        <Select
          label="Preferred Mount"
          data={[
            { value: 'left', label: 'Left' },
            { value: 'right', label: 'Right' },
          ]}
          value={preferred_mount}
          onChange={(v) => setPreferred_mount(v ?? 'right')}
        />
        <TagsInput
          label="Tip Connections"
          description="Labware IDs of compatible tip racks"
          placeholder="Type and press Enter"
          value={tip_connections}
          onChange={setTip_connections}
        />
        <Group justify="flex-end" mt="md">
          <Button variant="default" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit} loading={addMutation.isPending || updateMutation.isPending}>
            {isEdit ? 'Update' : 'Add'}
          </Button>
        </Group>
      </Stack>
    </Modal>
  )
}

// --- Main Editor ---

export function LabwareEditor() {
  const { data: labware, isLoading } = useLabwareQuery()
  const deletePipetteMutation = useDeletePipetteEntry()

  const [pipetteModal, setPipetteModal] = useState<{ opened: boolean; initial?: PipetteEntry; editIndex?: number }>({ opened: false })

  if (isLoading || !labware) return null

  const pipettes = labware.pipettes ?? []

  const handleDeletePipette = (index: number, name: string) => {
    deletePipetteMutation.mutate(index, {
      onSuccess: () => notifications.show({ color: 'teal', message: `Removed ${name}`, position: 'top-right' }),
      onError: (err) => notifications.show({ color: 'red', title: 'Error', message: err instanceof Error ? err.message : 'Unknown error', position: 'top-right' }),
    })
  }

  return (
    <Paper p="md" withBorder>
      <Title order={5} mb="sm">Hardware Catalog (labware_dict.toml)</Title>
      <Accordion variant="separated">
        {/* Pipettes Section */}
        <Accordion.Item value="pipettes">
          <Accordion.Control>
            <Group gap="xs">
              <Text fw={500}>Pipettes</Text>
              <Badge size="sm" variant="light">{pipettes.length}</Badge>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="xs">
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '4px 8px' }}>Name</th>
                    <th style={{ textAlign: 'left', padding: '4px 8px' }}>Opentrons ID</th>
                    <th style={{ textAlign: 'left', padding: '4px 8px' }}>Ch</th>
                    <th style={{ textAlign: 'left', padding: '4px 8px' }}>Volume Range</th>
                    <th style={{ textAlign: 'left', padding: '4px 8px' }}>Mount</th>
                    <th style={{ textAlign: 'left', padding: '4px 8px', width: 80 }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pipettes.map((p, i) => (
                    <tr key={`${p.name}-${i}`}>
                      <td style={{ padding: '4px 8px' }}><Text size="sm" fw={500}>{p.name}</Text></td>
                      <td style={{ padding: '4px 8px' }}><Text size="sm" c="dimmed">{p.opentrons_id}</Text></td>
                      <td style={{ padding: '4px 8px' }}><Badge size="xs" variant="light">{p.channels}</Badge></td>
                      <td style={{ padding: '4px 8px' }}><Text size="sm">{p.volume_range[0]}-{p.volume_range[1]} uL</Text></td>
                      <td style={{ padding: '4px 8px' }}><Text size="sm">{p.preferred_mount}</Text></td>
                      <td style={{ padding: '4px 8px' }}>
                        <Group gap={4}>
                          <Tooltip label="Edit">
                            <ActionIcon size="sm" variant="subtle" onClick={() => setPipetteModal({ opened: true, initial: p, editIndex: i })}>
                              <IconEdit size={14} />
                            </ActionIcon>
                          </Tooltip>
                          <Tooltip label="Delete">
                            <ActionIcon size="sm" variant="subtle" color="red" onClick={() => handleDeletePipette(i, p.name)}>
                              <IconTrash size={14} />
                            </ActionIcon>
                          </Tooltip>
                        </Group>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <Button
                size="xs"
                variant="light"
                leftSection={<IconPlus size={14} />}
                onClick={() => setPipetteModal({ opened: true })}
              >
                Add Pipette
              </Button>
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>

      {/* Modal - key forces remount to reset form state */}
      {pipetteModal.opened && (
        <PipetteFormModal
          key={`pipette-${pipetteModal.editIndex ?? 'new'}`}
          opened={pipetteModal.opened}
          onClose={() => setPipetteModal({ opened: false })}
          initial={pipetteModal.initial}
          editIndex={pipetteModal.editIndex}
        />
      )}
    </Paper>
  )
}
