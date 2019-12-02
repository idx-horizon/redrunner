echo Copying master repository and keys

docker cp gmap.key red:/redrunner/resources/gmap.key

docker cp masterREPOSITORY.db red:/redrunner/REPOSITORY.db
