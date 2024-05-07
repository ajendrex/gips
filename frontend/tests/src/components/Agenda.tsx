import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  VStack,
  Heading,
  useToast,
  SimpleGrid,
  Text,
} from '@chakra-ui/react'
import axios from 'axios'
import { getCsrfToken } from "../csrf";
import { ArrowLeftIcon, ArrowRightIcon } from "@chakra-ui/icons";
import {useMutation} from "react-query";

type Bloque = {
  inicio: string
  fin: string
}

type FechaDisponible = {
  fecha: string
  bloques: Bloque[]
}

const hora = (datetime: string): string => {
  return datetime.split(' ')[1]
}

const Agenda = ({codigo, successCallback}: {codigo: string, successCallback: () => void}) => {
  const [availableDates, setAvailableDates] = useState<FechaDisponible[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [selectedTime, setSelectedTime] = useState<Bloque | null>(null)
  const toast = useToast()
  const agendarEntrevista = useMutation(
    ({fecha}: {fecha: string}) => axios.post(
      `/api/entrevistas/crear-entrevista/?codigo=${codigo}`,
      { fecha: selectedTime?.inicio },
      {
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'Content-Type': 'application/json',
        },
      }),
      {
        onSuccess: () => {
          successCallback()
        },
        onError: (error: any) => {
          toast({
            title: "Error agendando entrevista",
            description: error.toString(),
            status: "error",
            duration: 9000,
            isClosable: true
          })
        }
      }
  )

  useEffect(() => {
    // scroll to top
    window.scrollTo(0, 0)
  })

  useEffect( () => {
    axios.get(`/api/entrevistas/horarios-disponibles/?codigo=${codigo}`).then(response => {
      setAvailableDates(response.data.dias)
    }).catch(error => {
      toast({
        title: "Error cargando horarios disponibles",
        description: error.toString(),
        status: "error",
        duration: 9000,
        isClosable: true
      })
    })
  }, [codigo, toast])

  const handleNextDay = () => {
    setCurrentIndex(current => current + 1)
  }

  const handlePreviousDay = () => {
    setCurrentIndex(current => current - 1)
  }

  const handleTimeBlockClick = (timeBlock: Bloque) => {
    setSelectedTime(timeBlock)
  }

  const handleSubmit = () => {
    agendarEntrevista.mutate({fecha: selectedTime!.inicio})
  }

  const currentDay = availableDates[currentIndex]
  const nombreDia = currentDay?.fecha.split('|')[0] || "Cargando.."
  const fecha = currentDay?.fecha.split('|')[1] || ""

  return (
    <VStack spacing={4} p={4}>
      <Box display="flex" justifyContent="space-between" width="100%">
        <Button onClick={handlePreviousDay} isDisabled={currentIndex === 0}><ArrowLeftIcon /></Button>
        <Heading size="lg" textAlign="center">{nombreDia}<br />{fecha}</Heading>
        <Button onClick={handleNextDay} isDisabled={currentIndex === availableDates.length - 1}><ArrowRightIcon /></Button>
      </Box>
      <Text>Entrevista de 20 minutos.</Text>
      <SimpleGrid columns={3} spacing={4}>
        {currentDay?.bloques.map((block, index) => (
          <Button
            key={index}
            onClick={() => handleTimeBlockClick(block)}
            colorScheme={selectedTime === block ? "teal" : "gray"}
            variant={selectedTime === block ? "solid" : "outline"}
          >
            {`${hora(block.inicio)}`}
          </Button>
        ))}
      </SimpleGrid>
      <Button colorScheme="blue" onClick={handleSubmit} isDisabled={!selectedTime}>Agendar!</Button>
    </VStack>
  )
}

export default Agenda
