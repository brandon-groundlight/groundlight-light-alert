import pygame

pygame.mixer.init()
sound_mixer = pygame.mixer.music.load("media/dog_barking.mp3")
pygame.mixer.music.play()