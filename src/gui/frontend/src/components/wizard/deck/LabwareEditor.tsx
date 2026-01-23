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
  Table,
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
  useAddLabwareEntry,
  useUpdateLabwareEntry,
  useDeleteLabwareEntry,
  useAddPipetteEntry,
  useUpdatePipetteEntry,
  useDeletePipetteEntry,
} from '../../../api/hooks'
import type { LabwareEntry, PipetteEntry } from '../../../api/types'

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
    }).catch((err) => {
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

// --- Labware Form Modal ---

interface LabwareFormProps {
  opened: boolean
  onClose: () => void
  initial?: LabwareEntry
  editIndex?: number
}

function LabwareFormModal({ opened, onClose, initial, editIndex }: LabwareFormProps) {
  const addMutation = useAddLabwareEntry()
  const updateMutation = useUpdateLabwareEntry()

  const [category, setCategory] = useState(initial?.category ?? 'plate')
  const [labware_id, setLabware_id] = useState(initial?.labware_id ?? '')
  const [well_count, setWell_count] = useState<number>(initial?.well_count ?? 96)
  const [well_volume, setWell_volume] = useState<number>(initial?.well_volume ?? 200)
  const [offset_x, setOffset_x] = useState<number | undefined>(initial?.offset_x)
  const [offset_y, setOffset_y] = useState<number | undefined>(initial?.offset_y)
  const [offset_z, setOffset_z] = useState<number | undefined>(initial?.offset_z)

  const isEdit = editIndex !== undefined

  const handleSubmit = () => {
    if (!labware_id) {
      notifications.show({ color: 'red', message: 'Labware ID is required', position: 'top-right' })
      return
    }
    const payload: LabwareEntry = {
      category,
      labware_id,
      well_count,
      well_volume,
      ...(offset_x !== undefined && offset_x !== 0 ? { offset_x } : {}),
      ...(offset_y !== undefined && offset_y !== 0 ? { offset_y } : {}),
      ...(offset_z !== undefined && offset_z !== 0 ? { offset_z } : {}),
    }
    const mutation = isEdit
      ? updateMutation.mutateAsync({ index: editIndex, payload })
      : addMutation.mutateAsync(payload)

    mutation.then(() => {
      notifications.show({ color: 'teal', message: isEdit ? 'Labware updated' : 'Labware added', position: 'top-right' })
      onClose()
    }).catch((err) => {
      notifications.show({ color: 'red', title: 'Error', message: err instanceof Error ? err.message : 'Unknown error', position: 'top-right' })
    })
  }

  return (
    <Modal opened={opened} onClose={onClose} title={isEdit ? 'Edit Labware' : 'Add Labware'} size="md">
      <Stack gap="sm">
        <Select
          label="Category"
          data={[
            { value: 'plate', label: 'Plate' },
            { value: 'tube_rack', label: 'Tube Rack' },
            { value: 'tip_rack', label: 'Tip Rack' },
            { value: 'reservoir', label: 'Reservoir' },
          ]}
          value={category}
          onChange={(v) => setCategory(v ?? 'plate')}
        />
        <TextInput label="Labware ID" placeholder="384_ppv_55ul" value={labware_id} onChange={(e) => setLabware_id(e.target.value)} required />
        <Group grow>
          <NumberInput label="Well Count" value={well_count} onChange={(v) => setWell_count(Number(v))} min={1} />
          <NumberInput label="Well Volume (uL)" value={well_volume} onChange={(v) => setWell_volume(Number(v))} min={1} />
        </Group>
        <Text size="sm" fw={500} mt="xs">Calibration Offsets (mm, optional)</Text>
        <Group grow>
          <NumberInput label="X" value={offset_x ?? ''} onChange={(v) => setOffset_x(v === '' ? undefined : Number(v))} step={0.05} decimalScale={3} placeholder="0" />
          <NumberInput label="Y" value={offset_y ?? ''} onChange={(v) => setOffset_y(v === '' ? undefined : Number(v))} step={0.05} decimalScale={3} placeholder="0" />
          <NumberInput label="Z" value={offset_z ?? ''} onChange={(v) => setOffset_z(v === '' ? undefined : Number(v))} step={0.05} decimalScale={3} placeholder="0" />
        </Group>
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
  const deleteLabwareMutation = useDeleteLabwareEntry()
  const deletePipetteMutation = useDeletePipetteEntry()

  const [pipetteModal, setPipetteModal] = useState<{ opened: boolean; initial?: PipetteEntry; editIndex?: number }>({ opened: false })
  const [labwareModal, setLabwareModal] = useState<{ opened: boolean; initial?: LabwareEntry; editIndex?: number }>({ opened: false })

  if (isLoading || !labware) return null

  const pipettes = labware.pipettes ?? []
  const labwareEntries = labware.labware ?? []

  const handleDeleteLabware = (index: number, id: string) => {
    deleteLabwareMutation.mutate(index, {
      onSuccess: () => notifications.show({ color: 'teal', message: `Removed ${id}`, position: 'top-right' }),
      onError: (err) => notifications.show({ color: 'red', title: 'Error', message: err instanceof Error ? err.message : 'Unknown error', position: 'top-right' }),
    })
  }

  const handleDeletePipette = (index: number, name: string) => {
    deletePipetteMutation.mutate(index, {
      onSuccess: () => notifications.show({ color: 'teal', message: `Removed ${name}`, position: 'top-right' }),
      onError: (err) => notifications.show({ color: 'red', title: 'Error', message: err instanceof Error ? err.message : 'Unknown error', position: 'top-right' }),
    })
  }

  const categoryColor = (cat: string) => {
    switch (cat) {
      case 'plate': return 'blue'
      case 'tube_rack': return 'grape'
      case 'tip_rack': return 'green'
      case 'reservoir': return 'cyan'
      default: return 'gray'
    }
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
              <Table striped highlightOnHover withTableBorder>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Name</Table.Th>
                    <Table.Th>Opentrons ID</Table.Th>
                    <Table.Th>Ch</Table.Th>
                    <Table.Th>Volume Range</Table.Th>
                    <Table.Th>Mount</Table.Th>
                    <Table.Th w={80}>Actions</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {pipettes.map((p, i) => (
                    <Table.Tr key={`${p.name}-${i}`}>
                      <Table.Td><Text size="sm" fw={500}>{p.name}</Text></Table.Td>
                      <Table.Td><Text size="sm" c="dimmed">{p.opentrons_id}</Text></Table.Td>
                      <Table.Td><Badge size="xs" variant="light">{p.channels}</Badge></Table.Td>
                      <Table.Td><Text size="sm">{p.volume_range[0]}-{p.volume_range[1]} uL</Text></Table.Td>
                      <Table.Td><Text size="sm">{p.preferred_mount}</Text></Table.Td>
                      <Table.Td>
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
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
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

        {/* Labware Section */}
        <Accordion.Item value="labware">
          <Accordion.Control>
            <Group gap="xs">
              <Text fw={500}>Labware Definitions</Text>
              <Badge size="sm" variant="light">{labwareEntries.length}</Badge>
            </Group>
          </Accordion.Control>
          <Accordion.Panel>
            <Stack gap="xs">
              <Table striped highlightOnHover withTableBorder>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Category</Table.Th>
                    <Table.Th>Labware ID</Table.Th>
                    <Table.Th>Wells</Table.Th>
                    <Table.Th>Volume</Table.Th>
                    <Table.Th>Offsets</Table.Th>
                    <Table.Th w={80}>Actions</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {labwareEntries.map((lw, i) => {
                    const hasOffsets = (lw.offset_x && lw.offset_x !== 0) || (lw.offset_y && lw.offset_y !== 0) || (lw.offset_z && lw.offset_z !== 0)
                    return (
                      <Table.Tr key={`${lw.labware_id}-${i}`}>
                        <Table.Td><Badge size="xs" color={categoryColor(lw.category)} variant="light">{lw.category}</Badge></Table.Td>
                        <Table.Td><Text size="sm" fw={500}>{lw.labware_id}</Text></Table.Td>
                        <Table.Td><Text size="sm">{lw.well_count}</Text></Table.Td>
                        <Table.Td><Text size="sm">{lw.well_volume} uL</Text></Table.Td>
                        <Table.Td>
                          {hasOffsets ? (
                            <Tooltip label={`x=${lw.offset_x ?? 0}, y=${lw.offset_y ?? 0}, z=${lw.offset_z ?? 0}`}>
                              <Badge size="xs" variant="dot" color="orange">set</Badge>
                            </Tooltip>
                          ) : (
                            <Text size="xs" c="dimmed">none</Text>
                          )}
                        </Table.Td>
                        <Table.Td>
                          <Group gap={4}>
                            <Tooltip label="Edit">
                              <ActionIcon size="sm" variant="subtle" onClick={() => setLabwareModal({ opened: true, initial: lw, editIndex: i })}>
                                <IconEdit size={14} />
                              </ActionIcon>
                            </Tooltip>
                            <Tooltip label="Delete">
                              <ActionIcon size="sm" variant="subtle" color="red" onClick={() => handleDeleteLabware(i, lw.labware_id)}>
                                <IconTrash size={14} />
                              </ActionIcon>
                            </Tooltip>
                          </Group>
                        </Table.Td>
                      </Table.Tr>
                    )
                  })}
                </Table.Tbody>
              </Table>
              <Button
                size="xs"
                variant="light"
                leftSection={<IconPlus size={14} />}
                onClick={() => setLabwareModal({ opened: true })}
              >
                Add Labware
              </Button>
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>

      {/* Modals - key forces remount to reset form state */}
      {pipetteModal.opened && (
        <PipetteFormModal
          key={`pipette-${pipetteModal.editIndex ?? 'new'}`}
          opened={pipetteModal.opened}
          onClose={() => setPipetteModal({ opened: false })}
          initial={pipetteModal.initial}
          editIndex={pipetteModal.editIndex}
        />
      )}
      {labwareModal.opened && (
        <LabwareFormModal
          key={`labware-${labwareModal.editIndex ?? 'new'}`}
          opened={labwareModal.opened}
          onClose={() => setLabwareModal({ opened: false })}
          initial={labwareModal.initial}
          editIndex={labwareModal.editIndex}
        />
      )}
    </Paper>
  )
}
