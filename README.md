# Anonymized-CNN-Daily-News-Stories

In order to anonymize CNN and Daily News Stories as can be found [here](http://cs.nyu.edu/~kcho/DMQA/), first download both Questions and Stories tar files, as entities are denoted only for the questions files.

First we need to find the mapping between questions data and stories, run the following:
```
python create_anonymized_stories.py 
          --mode map_qd 
          --questions_path /path/to/questions/cnn.tgz
```

After writing to file the mapping run this:
```
python create_anonymized_stories.py 
          --mode anonymize
          --stories_path /path/to/stories/cnn_stories.tgz 
          --out_dir /path/to/new/anonymized-stories
```
