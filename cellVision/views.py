from django.shortcuts import render, get_object_or_404
from django.http  import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.core.files import File 
from django.conf import settings
from django.utils import timezone

from .forms import CellVisionForm
import image_handler
from .models import CellImage
import json

from . import tasks

# Create your views here.

def classify(request):
    if request.method == 'POST':
        form = CellVisionForm(request.POST, request.FILES)
        if form.is_valid():
            upload = CellImage(image = request.FILES['image'], channels = form.cleaned_data['channels'], frames = form.cleaned_data['frames'], target = form.cleaned_data['target'])
            upload.save()            
            path = upload.image.path #absolute path of image
            name = upload.image.name #name of the image
            url = upload.image.url
            choices = form.cleaned_data['options'] #choices in list form       
            try:
                meta = image_handler.get_flex_data(path)
                upload.channels = meta[2]
                upload.frames = meta[0]
            except TypeError: 
                pass
            upload.name = name.split('.')[0]
            upload.email = form.cleaned_data['email']
            upload.save()            
            tasks._classify.delay(path, name, upload.frames, upload.channels, upload.target, choices, upload)
            return HttpResponseRedirect(reverse("cellVision:results", args=(upload.name,)))
    else:
        form = CellVisionForm()
	context_data = {'form': form}
    return render(request, 'cellVision/classify.html', {'form': form})

def download(request, file_name):
    file_location = str(settings.MEDIA_ROOT + "/classes/" + file_name +".xlsx")
    excel = File(open(file_location))
    response = HttpResponse(excel, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=' + file_name +'.xlsx'
    return response

def results(request, file_name):
    p = get_object_or_404(CellImage, name=file_name)
    p.last_accessed = timezone.now()
    p.save()
    if p.activations == [] and p.email == '':
        return(render(request, "cellVision/waiting1.html"))
    elif p.activations == []:
        return(render(request, "cellVision/waiting.html"))
    else:
        return render(request, "cellVision/classify_result.html", {'activations': json.dumps(p.activations), 'url': settings.MEDIA_URL + 'classes/' + p.image.name.split('.')[0], 'image': settings.MEDIA_URL + 'classes/' + p.image.name.split('.')[0]+"_FULL2", "name": p.name })

def sample(request, num):
    file_location = str(settings.MEDIA_ROOT + "/sample/sample_" + num+ ".flex" )
    array = File(open(file_location))
    response = HttpResponse(array, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=sample_' +num+'.flex'
    return response
