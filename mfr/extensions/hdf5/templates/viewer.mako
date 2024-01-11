<link rel="stylesheet" href="${base}/css/style.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
<link rel="stylesheet" href="${base}/css/bootstrap.min.css">
<link rel="stylesheet" href="${base}/css/bootstrap-treeview.min.css">

<div id="mfrViewer" style="min-height: 600px;">
 <div>    
    <a href="#" style="float: right;text-decoration: none; border: 1px solid #b5abab;color: #393434;background: #eee;padding: 3px 22px;margin: 10px 0px;"" id="return">${button}</a>
 </div>
 <div style="border-bottom:2px solid #dfd4d4; margin: 10px 0px; clear:both;"></div>
 <div style="float: left; width: 20%px%;">
    <div style="background: #f0efef; padding: 10px; border: 1px solid #e8e7e7; border-bottom: none; height:45px; padding: 5px;">
        <div style="background: #fff9f9; color: #4f68ee; border: 1px solid #eee; float: left; height: 90%;" id="folderContainer">
            <div style="padding: 6px;" id="folderElement">
                <i class="fa fa-search"></i>
                <span id="folderText">Folder</span>
            </div>
        </div>
        <div style="float:left;">
            <div id="textBoxContainer" style="display: none;">
                <input type="text" id="searchInput" placeholder="Folder..." style="width: 77%; height: 90%; padding: 4px; border: 1px solid #eee; float:left;">
                <div id="clearButton" style="background:#fff; float:left; padding: 9px; margin-left: 10px; height: 90%;">
                    <i class="fa fa-times"></i>
                </div>
            </div>
        </div>
        <div class="fangorn-toolbar-icon" style="background:#fff; float:left; padding: 9px; margin-left: 10px; height: 86%;" id="toggleIcon">
            <i class="fa fa-angle-up" id="icon"></i>
        </div>
    </div>
    <p id="noResults" style="display: none; padding: 10px;color: #958484; border: 1px solid #e3dcdc; text-align: center;">No results found.</p>        
    <div id="treeView">
        <div style="border: 1px solid #eee;color: #605f5f;height: 10%;padding: 20px;">
            Loading files...
        </div>
    </div>
 </div>
 <div style="height:0px;">
    <span id="datasetName"></span>
    <div id="fileContent">   
        ${div}    
    </div>
 </div>
 <div style="clear: both;" id="file_attribute">
   ${file_attribute}
 </div>
</div>

<script src="/static/js/jquery-1.11.3.min.js"></script>
<script src="${base}/js/bootstrap.min.js"></script>
<script src="${base}/js/bootstrap-treeview.min.js"></script>
<script src="/static/js/mfr.js"></script>
<script src="/static/js/mfr-child.js"></script>
<script>    
    
    $("#return").on('click', function(){
        window.history.back();
    });
    
    var treeExpanded = true;
    $('#toggleIcon').on('click', function(){
        $('#treeView').slideToggle('fast');
        $('#icon').toggleClass('fa-angle-up fa-angle-down');
    });

    var $matchingItems = '';

    var treeData = ${tree_data};
    var previous_file_name = '';
    var previous_attribute = '';

    $('#treeView').treeview({
        data: treeData,
        levels: 20,
        showTags: true,
        expandIcon: 'fas fa-chevron-right',
        collapseIcon: 'fas fa-chevron-down',
        emptyIcon: 'fas fa-file',
        onNodeSelected: function(event, node){
            if(node.nodes){                
                return;
            }                                 

            var file_name = node.file_name;  
            console.log(file_name);          
            if(previous_file_name != ''){
                console.log(previous_file_name);
                $('#' + previous_file_name).css('display', 'none');
                $('#' + previous_attribute).css('display', 'none');
            }            
            
            $('#' + file_name).css('display', 'block');  
            $('#' + file_name + '_attribute').css('display', 'block');    
            var uuid = $('#' + file_name +' div').data('uuid');      
            console.log(uuid);    
            $("#tabular-tabs"+uuid+" a:first").click();
            
            previous_file_name = file_name;
            previous_attribute = file_name+'_attribute';
            
            $('#datasetName').text((node.path).split('/').pop());                                            
        }
    });
  

    var $folderElement = $("#folderElement");
    var $folderText = $("#folderText");
    var $folderContainer = $("#folderContainer");
    var $textBoxContainer = $("#textBoxContainer");
    var $searchInput = $("#searchInput");
    var $clearButton = $("#clearButton");
    var originalNodeTreeView = $('#treeView').html();

    $folderElement.on("click", function(){
        $folderContainer.hide();
        $textBoxContainer.show();
        $searchInput.focus();
        $('#toggleIcon').hide();
    });

    $clearButton.on("click", function(){
        $folderContainer.show();
        $textBoxContainer.hide();
        $('#noResults').hide();
        $('#treeView').html('');
        $('#treeView').html(originalNodeTreeView);
        $('#toggleIcon').show();
    });
    
    $('#searchInput').on('input', function() {
        var searchText = $(this).val().toLowerCase();               

        $('.node-treeView').hide();
        
        $matchingItems = $('.node-treeView').filter(function() {
            return $(this).text().toLowerCase().indexOf(searchText) > -1;
        });

        $matchingItems.each(function(){
            $(this).html($(this).html().replace(/<span class="indent"><\/span>/g, ''));                    
        });        

        if ($matchingItems.length === 0){
            $('#noResults').show();
        } else {           
            $('#noResults').hide();
            $matchingItems.show();
        }
    });    
</script>